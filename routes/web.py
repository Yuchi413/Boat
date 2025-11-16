from flask import Blueprint, render_template, request, abort
from line_push2 import handler, line_bot_api
from linebot.models import (
    TextSendMessage,
    MessageEvent,
    TextMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
)
from linebot.exceptions import InvalidSignatureError

# =========================================
# 建立 Blueprint
# =========================================
web_blueprint = Blueprint("web", __name__)

# =========================================
# 首頁 (前端地圖)
# =========================================
@web_blueprint.route("/")
def show_map():
    return render_template("ship.html")


# =========================================
# LINE Webhook
# =========================================
@web_blueprint.route("/callback", methods=["POST"])
def callback():
    """LINE webhook endpoint"""
    if not handler:
        abort(503, description="LINE handler not configured")

    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400, description="Invalid signature")
    except Exception as e:
        print(f"[Webhook] Error: {e}")
        abort(500, description=str(e))

    return "OK"


# =========================================
# LINE Message Event Handler
# =========================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理使用者文字訊息"""
    user_input = event.message.text.strip()

    # Step 1. 顯示選單
    if user_input in ["menu", "選單"]:
        reply = TextSendMessage(
            text="請選擇操作：",
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(action=MessageAction(label="查詢 ID", text="查詢 ID")),
                ]
            ),
        )
        line_bot_api.reply_message(event.reply_token, reply)
        return

    # Step 2. 查詢 ID
    elif user_input.lower() in ["查詢 id", "userid", "groupid", "roomid"]:
        source = event.source
        if source.type == "user":
            reply_text = f"👤 使用者 ID：\n{source.user_id}"
        elif source.type == "group":
            reply_text = f"👥 群組 ID：\n{source.group_id}"
        elif source.type == "room":
            reply_text = f"💬 聊天室 ID：\n{source.room_id}"
        else:
            reply_text = "❌ 無法辨識來源類型。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    # Step 3. 其他輸入
    else:
        reply = TextSendMessage(text="請輸入「menu」開啟功能選單。")
        line_bot_api.reply_message(event.reply_token, reply)

    print(f"[LINE DEBUG] 收到訊息：{event.message.text}, 來源：{event.source.type}")

