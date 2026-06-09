import os
import json
from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, stream_with_context
from dotenv import load_dotenv
from database import init_db, create_study, get_study, list_studies, create_session, get_session, update_session_messages, complete_session, get_sessions_for_study, delete_study
from interview_bot import stream_response, get_first_message, DEFAULT_GENERAL_INSTRUCTIONS

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

init_db()


@app.route("/")
def index():
    studies = list_studies()
    return render_template("index.html", studies=studies, default_instructions=DEFAULT_GENERAL_INSTRUCTIONS)


@app.route("/create-study", methods=["POST"])
def create_study_route():
    title = request.form.get("title", "").strip()
    research_question = request.form.get("research_question", "").strip()
    interview_outline = request.form.get("interview_outline", "").strip()
    general_instructions = request.form.get("general_instructions", "").strip()
    model = request.form.get("model", "claude-sonnet-4-20250514")

    if not title or not research_question or not interview_outline:
        return jsonify({"error": "Title, research question, and interview outline are required"}), 400

    study_id = create_study(title, research_question, interview_outline, general_instructions, model)
    return redirect(url_for("study_created", study_id=study_id))


@app.route("/study/<study_id>/created")
def study_created(study_id):
    study = get_study(study_id)
    if not study:
        return "Study not found", 404
    interview_url = request.url_root.rstrip("/") + url_for("interview_page", study_id=study_id)
    return render_template("study_created.html", study=study, interview_url=interview_url)


@app.route("/interview/<study_id>")
def interview_page(study_id):
    study = get_study(study_id)
    if not study:
        return "Interview not found", 404
    return render_template("interview.html", study=study)


@app.route("/api/session/create", methods=["POST"])
def api_create_session():
    data = request.get_json()
    study_id = data.get("study_id")
    respondent_name = data.get("respondent_name", "")
    if not study_id or not get_study(study_id):
        return jsonify({"error": "Invalid study"}), 400
    session_id = create_session(study_id, respondent_name)
    return jsonify({"session_id": session_id})


@app.route("/api/session/<session_id>/first-message")
def api_first_message(session_id):
    session = get_session(session_id)
    if not session:
        return "Session not found", 404
    study = get_study(session["study_id"])
    if not study:
        return "Study not found", 404

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not configured"}), 500

    def generate():
        full_text = ""
        for chunk in get_first_message(study, api_key):
            full_text += chunk
            yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"

        messages = [
            {"role": "user", "content": "Hello, I'm ready to start the interview."},
            {"role": "assistant", "content": full_text},
        ]
        update_session_messages(session_id, messages)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.route("/api/session/<session_id>/message", methods=["POST"])
def api_send_message(session_id):
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    if session["status"] != "active":
        return jsonify({"error": "Interview already completed"}), 400

    study = get_study(session["study_id"])
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not configured"}), 500

    messages = session["messages"]
    messages.append({"role": "user", "content": user_message})
    update_session_messages(session_id, messages)

    def generate():
        full_response = ""
        final_code = None
        closing = None

        for event in stream_response(study, messages, api_key):
            if event["type"] == "text":
                full_response += event["content"]
                yield f"data: {json.dumps({'type': 'text', 'content': event['content']})}\n\n"
            elif event["type"] == "done":
                final_code = event.get("code")
                closing = event.get("closing")

        messages.append({"role": "assistant", "content": full_response})
        update_session_messages(session_id, messages)

        if final_code == "complete" or final_code == "safety":
            complete_session(session_id)
            yield f"data: {json.dumps({'type': 'closing', 'message': closing})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.route("/dashboard")
def dashboard():
    studies = list_studies()
    return render_template("dashboard.html", studies=studies)


@app.route("/dashboard/<study_id>")
def study_dashboard(study_id):
    study = get_study(study_id)
    if not study:
        return "Study not found", 404
    sessions = get_sessions_for_study(study_id)
    interview_url = request.url_root.rstrip("/") + url_for("interview_page", study_id=study_id)
    return render_template("study_dashboard.html", study=study, sessions=sessions, interview_url=interview_url)


@app.route("/api/study/<study_id>/export")
def api_export_transcripts(study_id):
    study = get_study(study_id)
    if not study:
        return jsonify({"error": "Study not found"}), 404
    sessions = get_sessions_for_study(study_id)

    transcripts = []
    for s in sessions:
        lines = []
        for m in s["messages"]:
            role = "Interviewer" if m["role"] == "assistant" else "Respondent"
            lines.append(f"{role}: {m['content']}")
        transcripts.append({
            "session_id": s["id"],
            "respondent": s["respondent_name"] or "Anonymous",
            "status": s["status"],
            "started_at": s["started_at"],
            "completed_at": s["completed_at"],
            "duration_seconds": s["duration_seconds"],
            "message_count": len(s["messages"]),
            "transcript": "\n\n".join(lines),
        })

    return jsonify({"study": study["title"], "transcripts": transcripts})


@app.route("/api/study/<study_id>", methods=["DELETE"])
def api_delete_study(study_id):
    delete_study(study_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
