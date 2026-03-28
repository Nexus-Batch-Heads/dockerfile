"""
Nexus AI – Digital Twin Routes (Production)
=============================================
REST API endpoints for avatar generation, voice cloning,
twin interaction, and lip-sync. All data persisted in MSSQL.
Generated files served via /api/twin/media/<filename>.
"""

import json
import logging
import os

from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.voice_clone_service import VoiceCloneService
from services.avatar_service import AvatarService

logger = logging.getLogger(__name__)

twin_bp = Blueprint("twin", __name__, url_prefix="/api/twin")

voice_service = VoiceCloneService()
avatar_service = AvatarService()

# ── Directories for serving generated files ─────────────────────
AVATAR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads", "avatars")
VOICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads", "voice")
os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs(VOICE_DIR, exist_ok=True)


# ── Media Serving ───────────────────────────────────────────────

@twin_bp.route("/media/<path:filename>", methods=["GET"])
def serve_media(filename):
    """Serve generated avatar PNGs and voice MP3s."""
    # Check avatars dir first, then voice dir
    avatar_path = os.path.join(AVATAR_DIR, filename)
    voice_path = os.path.join(VOICE_DIR, filename)

    if os.path.exists(avatar_path):
        return send_from_directory(os.path.abspath(AVATAR_DIR), filename)
    elif os.path.exists(voice_path):
        return send_from_directory(os.path.abspath(VOICE_DIR), filename)
    else:
        return jsonify({"success": False, "message": "File not found"}), 404


# ── Twin Profile ────────────────────────────────────────────────

@twin_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_twin_profile():
    """Get the user's complete digital twin profile from MSSQL."""
    user_id = get_jwt_identity()

    avatar = avatar_service.get_active_avatar(user_id)
    voice = voice_service.get_active_profile(user_id)

    # Parse JSON strings back to dicts for the response
    if avatar and avatar.get("facial_features"):
        try:
            avatar["facial_features"] = json.loads(avatar["facial_features"])
        except (json.JSONDecodeError, TypeError):
            pass

    if voice and voice.get("voice_characteristics"):
        try:
            voice["voice_characteristics"] = json.loads(voice["voice_characteristics"])
        except (json.JSONDecodeError, TypeError):
            pass

    return jsonify({
        "success": True,
        "twin": {
            "avatar": avatar,
            "voice": voice,
            "has_avatar": avatar is not None,
            "has_voice": voice is not None,
        },
    }), 200


# ── Avatar Generation ──────────────────────────────────────────

@twin_bp.route("/avatar/create", methods=["POST"])
@jwt_required()
def create_avatar():
    """
    Upload a face photo → generate a real avatar PNG → store in MSSQL.
    Returns the avatar URL and facial feature data.
    """
    user_id = get_jwt_identity()

    image_file = request.files.get("image")
    expression = request.form.get("expression", "neutral")
    skin_tone = request.form.get("skin_tone", "#e0b48c")

    # Generate the avatar image using Pillow
    avatar_data = avatar_service.generate_avatar(
        user_id=user_id,
        image_file=image_file,
        expression=expression,
        skin_tone=skin_tone,
    )

    # Save to MSSQL
    db_record = avatar_service.save_to_db(user_id, avatar_data)

    return jsonify({
        "success": True,
        "message": "Avatar generated and saved to database.",
        "avatar": {
            "avatar_url": avatar_data["avatar_url"],
            "face_image_url": avatar_data.get("face_image_url"),
            "facial_features": avatar_data["facial_features"],
            "expression": expression,
            "skin_tone": skin_tone,
            "db_record": db_record,
        },
    }), 201


@twin_bp.route("/avatar/profile", methods=["GET"])
@jwt_required()
def get_avatar_profile():
    """Get the user's active avatar profile from MSSQL."""
    user_id = get_jwt_identity()
    avatar = avatar_service.get_active_avatar(user_id)

    if avatar:
        if avatar.get("facial_features"):
            try:
                avatar["facial_features"] = json.loads(avatar["facial_features"])
            except (json.JSONDecodeError, TypeError):
                pass
        return jsonify({"success": True, "avatar": avatar}), 200

    return jsonify({"success": False, "message": "No avatar found. Upload a photo to create one."}), 404


@twin_bp.route("/avatar/expression", methods=["GET"])
@jwt_required()
def get_expression():
    """Get morph target values for a given expression state."""
    expression_name = request.args.get("name", "neutral")
    morph_targets = avatar_service.get_expression_state(expression_name)
    return jsonify({
        "success": True,
        "expression": expression_name,
        "morph_targets": morph_targets,
    }), 200


# ── Voice Clone ─────────────────────────────────────────────────

@twin_bp.route("/voice/enroll", methods=["POST"])
@jwt_required()
def enroll_voice():
    """
    Upload audio → analyse voice → generate cloned speech MP3 → store in MSSQL.
    Returns the cloned audio URL and voice characteristics.
    """
    user_id = get_jwt_identity()

    audio_file = request.files.get("audio")

    # Clone the voice: analyse + generate TTS sample
    clone_data = voice_service.clone_voice(user_id=user_id, audio_file=audio_file)

    # Save to MSSQL
    db_record = voice_service.save_to_db(user_id, clone_data)

    return jsonify({
        "success": True,
        "message": "Voice cloned and saved to database.",
        "voice": {
            "original_audio_url": clone_data.get("original_audio_url"),
            "cloned_audio_url": clone_data.get("cloned_audio_url"),
            "voice_characteristics": clone_data["voice_characteristics"],
            "edge_tts_voice": clone_data["edge_tts_voice"],
            "db_record": db_record,
        },
    }), 201


@twin_bp.route("/voice/profile", methods=["GET"])
@jwt_required()
def get_voice_profile():
    """Get the user's active voice profile from MSSQL."""
    user_id = get_jwt_identity()
    profile = voice_service.get_active_profile(user_id)

    if profile:
        if profile.get("voice_characteristics"):
            try:
                profile["voice_characteristics"] = json.loads(profile["voice_characteristics"])
            except (json.JSONDecodeError, TypeError):
                pass
        return jsonify({"success": True, "voice_profile": profile}), 200

    return jsonify({"success": False, "message": "No voice profile found. Upload audio to clone your voice."}), 404


@twin_bp.route("/voice/synthesize", methods=["POST"])
@jwt_required()
def synthesize_voice():
    """Generate speech from text using the user's cloned voice."""
    user_id = get_jwt_identity()
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return jsonify({"success": False, "message": "Text is required."}), 400

    result = voice_service.synthesize_speech(user_id, text)

    if result:
        return jsonify({
            "success": True,
            "message": "Speech synthesized with your cloned voice.",
            "audio_url": result["audio_url"],
            "voice": result["voice"],
        }), 200
    else:
        return jsonify({"success": False, "message": "Synthesis failed."}), 500


# ── Twin Chat ───────────────────────────────────────────────────

@twin_bp.route("/chat", methods=["POST"])
@jwt_required()
def twin_chat():
    """
    Chat with the digital twin. Returns AI response text,
    plus synthesised speech audio URL and avatar animation data.
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    message = data.get("message", "")

    if not message:
        return jsonify({"success": False, "message": "Message is required."}), 400

    # Get profiles
    voice = voice_service.get_active_profile(user_id)
    avatar = avatar_service.get_active_avatar(user_id)

    # Generate AI response
    try:
        from services.ai_service import AIService
        ai = AIService()
        result = ai.generate_response(message)
        response_text = result.get("response", "")
    except Exception as exc:
        logger.error("AI error in twin chat: %s", exc)
        response_text = "I'm having trouble responding right now. Please try again."

    # Synthesise response in cloned voice
    speech_data = None
    if voice:
        try:
            speech_data = voice_service.synthesize_speech(user_id, response_text[:500])
        except Exception as exc:
            logger.error("Speech synthesis failed: %s", exc)

    return jsonify({
        "success": True,
        "response": response_text,
        "speech": speech_data,
        "animation": {
            "expression": "speaking",
            "morph_targets": avatar_service.get_expression_state("speaking"),
        },
        "avatar_url": avatar.get("avatar_url") if avatar else None,
    }), 200


# ── Lip Sync ────────────────────────────────────────────────────

@twin_bp.route("/lipsync", methods=["POST"])
@jwt_required()
def get_lipsync_data():
    """Generate phoneme-level lip sync data from text."""
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return jsonify({"success": False, "message": "Text is required."}), 400

    visemes = []
    words = text.split()
    time_offset = 0.0
    avg_word_duration = 0.35

    viseme_map = {
        "a": "aa", "e": "E", "i": "ih", "o": "oh", "u": "ou",
        "b": "PP", "m": "PP", "p": "PP",
        "f": "FF", "v": "FF",
        "d": "DD", "t": "DD", "n": "nn",
        "k": "kk", "g": "kk", "c": "kk",
        "l": "nn", "r": "RR", "s": "SS", "z": "SS",
        "w": "ou", "y": "ih", "h": "aa",
    }

    for word in words:
        word_lower = word.lower().strip(".,!?;:'\"")
        if not word_lower:
            continue

        first = word_lower[0]
        viseme = viseme_map.get(first, "aa")

        visemes.append({
            "word": word,
            "viseme": viseme,
            "start": round(time_offset, 3),
            "end": round(time_offset + avg_word_duration, 3),
            "morph_targets": {
                "jawOpen": 0.3 if viseme in ["aa", "oh"] else 0.15,
                "mouthSmile": 0.1 if viseme in ["E", "ih"] else 0,
                "lipsPucker": 0.3 if viseme in ["ou", "PP"] else 0,
                "mouthOpen": 0.4 if viseme in ["aa", "oh"] else 0.2,
            },
        })
        time_offset += avg_word_duration

    return jsonify({
        "success": True,
        "text": text,
        "duration": round(time_offset, 3),
        "visemes": visemes,
        "word_count": len(words),
    }), 200
