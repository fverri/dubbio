import React, { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Video } from "lucide-react";
import "./App.css";

type Message = { from: string; text: string };
type ChatData = { messages: Message[] };
type ProfileData = { profileName: string };

export default function IMessageChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [profileName, setProfileName] = useState<string>("");
  const messageBoxRef = useRef<HTMLDivElement>(null);
  const strokeWidth = 1.5;

  useEffect(() => {
    const ac = new AbortController();
    (async () => {
      const [chatRes, profileRes] = await Promise.all([
        fetch("/chat.json", { signal: ac.signal }),
        fetch("/profile_name.json", { signal: ac.signal }),
      ]);
      const [chat, profile] = await Promise.all([
        chatRes.json() as Promise<ChatData>,
        profileRes.json() as Promise<ProfileData>,
      ]);
      setMessages(chat?.messages ?? []);
      setProfileName(profile?.profileName ?? "");
    })();
    return () => ac.abort();
  }, []);

  useEffect(() => {
    if (messageBoxRef.current) {
      messageBoxRef.current.scrollTop = messageBoxRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="container">
      <div className="chat-box">
        <div className="header">
          <ChevronLeft className="chevron-left" strokeWidth={strokeWidth} />
          <div className="profile">
            <img
              src="/profile_image.png"
              alt={profileName ? `${profileName} profile` : "Profile"}
              loading="lazy"
              decoding="async"
              className="profile-pic"
            />
            <div className="profile-info">
              <span className="profile-name">{profileName}</span>
              <ChevronRight
                className="chevron-right"
                strokeWidth={strokeWidth}
              />
            </div>
          </div>
          <Video className="video" strokeWidth={strokeWidth} />
        </div>

        <div className="imessage" ref={messageBoxRef}>
          {messages.map((msg, index) => {
            const isUser = msg.from === "me";
            const nextFrom =
              index < messages.length - 1 ? messages[index + 1].from : null;
            const prevFrom = index > 0 ? messages[index - 1].from : null;
            const isLastInBlock = nextFrom !== msg.from;
            const isNewBlock = prevFrom !== msg.from;

            const klass = [
              isUser ? "from-me" : "from-them",
              isLastInBlock && "last-in-block",
              isNewBlock && "new-block",
            ]
              .filter(Boolean)
              .join(" ");

            return (
              <p key={index} className={klass}>
                {msg.text}
              </p>
            );
          })}
        </div>
      </div>
    </div>
  );
}