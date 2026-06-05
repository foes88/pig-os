"use client";
import { useState } from "react";
import { useAuthStore } from "@/store/auth.store";

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const [name, setName] = useState(user?.name ?? "");
  const [phone, setPhone] = useState("");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const initials = name.slice(0, 2).toUpperCase() || "??";

  return (
    <div className="max-w-xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight mb-5">프로필 편집</h1>

      {saved && (
        <div className="mb-4 px-4 py-2.5 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700 font-medium">
          ✓ 변경사항이 저장됐습니다
        </div>
      )}

      <div className="flex items-center gap-4 mb-6">
        <div className="w-16 h-16 rounded-full bg-purple-600 text-white flex items-center justify-center text-xl font-bold">
          {initials}
        </div>
        <button className="px-4 py-2 rounded-xl border border-border bg-surface text-xs font-semibold text-text2 hover:bg-border transition">
          사진 변경
        </button>
      </div>

      <div className="bg-surface border border-border rounded-2xl p-6 space-y-4">
        {[
          { label: "이름", value: name, set: setName, type: "text", placeholder: "이름을 입력하세요" },
          { label: "이메일", value: user?.email ?? "", set: () => {}, type: "email", placeholder: "", disabled: true },
          { label: "전화번호", value: phone, set: setPhone, type: "tel", placeholder: "010-0000-0000" },
        ].map(({ label, value, set, type, placeholder, disabled }) => (
          <div key={label}>
            <label className="block text-xs font-semibold text-text3 mb-1.5">{label}</label>
            <input
              type={type}
              value={value}
              onChange={(e) => (set as (v: string) => void)(e.target.value)}
              placeholder={placeholder}
              disabled={disabled}
              className="input w-full disabled:opacity-50 disabled:bg-background"
            />
          </div>
        ))}
      </div>

      <button
        onClick={handleSave}
        className="w-full mt-4 bg-navy text-white py-3.5 rounded-xl text-sm font-bold hover:opacity-90 transition"
      >
        변경사항 저장
      </button>
    </div>
  );
}
