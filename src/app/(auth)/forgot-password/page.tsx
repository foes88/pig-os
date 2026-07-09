"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { authApi } from "@/lib/api/endpoints/auth";

// (auth) 공개 레이아웃 사용. middleware의 PUBLIC_PATHS에 /forgot-password 이미 포함.
// 이메일 실발송 채널은 아직 미설정(백엔드 _deliver_reset_token = 로그/운영자 중개) → 문구도 그에 맞춤.

const LANGS = ["en", "ko", "zh", "es", "vi", "th", "pt", "ru"] as const;
type Lang = (typeof LANGS)[number];
const SELECTABLE: Lang[] = LANGS.filter((l) => l !== "ko");

const T: Record<Lang, {
  reqTitle: string; reqSub: string; email: string; send: string; sending: string; sent: string;
  cfmTitle: string; cfmSub: string; newPw: string; confirmPw: string; reset: string; resetting: string;
  resetOk: string; pwMismatch: string; pwShort: string; badToken: string; err: string; back: string;
}> = {
  en: { reqTitle: "Reset password", reqSub: "Enter your account email. If it exists, a reset link will be issued.",
    email: "Email", send: "Send reset link", sending: "Sending…",
    sent: "Request received. If the account exists, your administrator will share a reset link or temporary password.",
    cfmTitle: "Set a new password", cfmSub: "Enter a new password for your account.",
    newPw: "New password", confirmPw: "Confirm password", reset: "Reset password", resetting: "Resetting…",
    resetOk: "Password changed. You can now sign in.", pwMismatch: "Passwords do not match.",
    pwShort: "Password must be at least 8 characters.", badToken: "This reset link is invalid or expired.",
    err: "Something went wrong. Please try again.", back: "Back to sign in" },
  ko: { reqTitle: "비밀번호 재설정", reqSub: "계정 이메일을 입력하세요. 존재하면 재설정 링크가 발급됩니다.",
    email: "이메일", send: "재설정 링크 보내기", sending: "전송 중…",
    sent: "요청이 접수되었습니다. 계정이 있으면 관리자가 재설정 링크 또는 임시 비밀번호를 전달합니다.",
    cfmTitle: "새 비밀번호 설정", cfmSub: "계정의 새 비밀번호를 입력하세요.",
    newPw: "새 비밀번호", confirmPw: "비밀번호 확인", reset: "비밀번호 재설정", resetting: "변경 중…",
    resetOk: "비밀번호가 변경되었습니다. 이제 로그인하세요.", pwMismatch: "비밀번호가 일치하지 않습니다.",
    pwShort: "비밀번호는 8자 이상이어야 합니다.", badToken: "재설정 링크가 유효하지 않거나 만료되었습니다.",
    err: "오류가 발생했습니다. 다시 시도하세요.", back: "로그인으로 돌아가기" },
  zh: { reqTitle: "重置密码", reqSub: "输入账户邮箱。若存在，将发放重置链接。",
    email: "邮箱", send: "发送重置链接", sending: "发送中…",
    sent: "请求已收到。若账户存在，管理员将转发重置链接或临时密码。",
    cfmTitle: "设置新密码", cfmSub: "为账户输入新密码。",
    newPw: "新密码", confirmPw: "确认密码", reset: "重置密码", resetting: "重置中…",
    resetOk: "密码已修改，现在可以登录。", pwMismatch: "两次密码不一致。",
    pwShort: "密码至少需 8 位。", badToken: "重置链接无效或已过期。",
    err: "出现错误，请重试。", back: "返回登录" },
  es: { reqTitle: "Restablecer contraseña", reqSub: "Ingresa el correo de tu cuenta. Si existe, se emitirá un enlace.",
    email: "Correo", send: "Enviar enlace", sending: "Enviando…",
    sent: "Solicitud recibida. Si la cuenta existe, tu administrador compartirá un enlace o contraseña temporal.",
    cfmTitle: "Nueva contraseña", cfmSub: "Ingresa una nueva contraseña para tu cuenta.",
    newPw: "Nueva contraseña", confirmPw: "Confirmar contraseña", reset: "Restablecer", resetting: "Procesando…",
    resetOk: "Contraseña cambiada. Ya puedes iniciar sesión.", pwMismatch: "Las contraseñas no coinciden.",
    pwShort: "La contraseña debe tener al menos 8 caracteres.", badToken: "El enlace es inválido o expiró.",
    err: "Algo salió mal. Inténtalo de nuevo.", back: "Volver a iniciar sesión" },
  vi: { reqTitle: "Đặt lại mật khẩu", reqSub: "Nhập email tài khoản. Nếu tồn tại, liên kết đặt lại sẽ được cấp.",
    email: "Email", send: "Gửi liên kết", sending: "Đang gửi…",
    sent: "Đã nhận yêu cầu. Nếu tài khoản tồn tại, quản trị viên sẽ gửi liên kết hoặc mật khẩu tạm thời.",
    cfmTitle: "Đặt mật khẩu mới", cfmSub: "Nhập mật khẩu mới cho tài khoản.",
    newPw: "Mật khẩu mới", confirmPw: "Xác nhận mật khẩu", reset: "Đặt lại", resetting: "Đang xử lý…",
    resetOk: "Đã đổi mật khẩu. Bạn có thể đăng nhập.", pwMismatch: "Mật khẩu không khớp.",
    pwShort: "Mật khẩu phải có ít nhất 8 ký tự.", badToken: "Liên kết không hợp lệ hoặc đã hết hạn.",
    err: "Đã xảy ra lỗi. Vui lòng thử lại.", back: "Quay lại đăng nhập" },
  th: { reqTitle: "รีเซ็ตรหัสผ่าน", reqSub: "กรอกอีเมลบัญชี หากมีอยู่ ระบบจะออกลิงก์รีเซ็ต",
    email: "อีเมล", send: "ส่งลิงก์รีเซ็ต", sending: "กำลังส่ง…",
    sent: "รับคำขอแล้ว หากมีบัญชีอยู่ ผู้ดูแลจะส่งลิงก์รีเซ็ตหรือรหัสผ่านชั่วคราวให้",
    cfmTitle: "ตั้งรหัสผ่านใหม่", cfmSub: "กรอกรหัสผ่านใหม่ของบัญชี",
    newPw: "รหัสผ่านใหม่", confirmPw: "ยืนยันรหัสผ่าน", reset: "รีเซ็ต", resetting: "กำลังรีเซ็ต…",
    resetOk: "เปลี่ยนรหัสผ่านแล้ว เข้าสู่ระบบได้เลย", pwMismatch: "รหัสผ่านไม่ตรงกัน",
    pwShort: "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร", badToken: "ลิงก์ไม่ถูกต้องหรือหมดอายุ",
    err: "เกิดข้อผิดพลาด โปรดลองใหม่", back: "กลับไปเข้าสู่ระบบ" },
  pt: { reqTitle: "Redefinir senha", reqSub: "Informe o e-mail da conta. Se existir, um link será emitido.",
    email: "E-mail", send: "Enviar link", sending: "Enviando…",
    sent: "Solicitação recebida. Se a conta existir, seu administrador enviará um link ou senha temporária.",
    cfmTitle: "Nova senha", cfmSub: "Informe uma nova senha para a conta.",
    newPw: "Nova senha", confirmPw: "Confirmar senha", reset: "Redefinir", resetting: "Processando…",
    resetOk: "Senha alterada. Você já pode entrar.", pwMismatch: "As senhas não coincidem.",
    pwShort: "A senha deve ter ao menos 8 caracteres.", badToken: "O link é inválido ou expirou.",
    err: "Algo deu errado. Tente novamente.", back: "Voltar ao login" },
  ru: { reqTitle: "Сброс пароля", reqSub: "Введите email аккаунта. Если он существует, будет выдана ссылка для сброса.",
    email: "Электронная почта", send: "Отправить ссылку", sending: "Отправка…",
    sent: "Запрос принят. Если аккаунт существует, администратор отправит ссылку для сброса или временный пароль.",
    cfmTitle: "Задать новый пароль", cfmSub: "Введите новый пароль для аккаунта.",
    newPw: "Новый пароль", confirmPw: "Подтвердите пароль", reset: "Сбросить пароль", resetting: "Сброс…",
    resetOk: "Пароль изменён. Теперь вы можете войти.", pwMismatch: "Пароли не совпадают.",
    pwShort: "Пароль должен содержать не менее 8 символов.", badToken: "Ссылка недействительна или устарела.",
    err: "Что-то пошло не так. Попробуйте снова.", back: "Вернуться ко входу" },
};

const INPUT = `w-full h-11 px-3.5 rounded-lg text-sm text-slate-900 placeholder:text-slate-400
  outline-none border bg-white transition focus:ring-2 focus:ring-[#2563EB]/20
  focus:border-[#2563EB] border-[#CBD5E1]`;

export default function ForgotPasswordPage() {
  const params = useSearchParams();
  const token = params.get("token");
  const [lang, setLang] = useState<Lang>("en");
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const m = document.cookie.match(/(?:^|;\s*)NEXT_LOCALE=([^;]+)/);
    const c = m?.[1] as Lang | undefined;
    if (c && SELECTABLE.includes(c)) setLang(c);
  }, []);
  const t = T[lang];

  async function onRequest(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await authApi.requestPasswordReset(email.trim());
      setDone(true);  // 열거방지: 성공/실패 무관 동일 메시지
    } catch {
      setDone(true);  // 요청 실패도 동일 처리(계정 존재 노출 금지)
    } finally {
      setBusy(false);
    }
  }

  async function onConfirm(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    if (pw.length < 8) return setErr(t.pwShort);
    if (pw !== pw2) return setErr(t.pwMismatch);
    setBusy(true);
    try {
      await authApi.confirmPasswordReset(token!, pw);
      setDone(true);
    } catch (e2: unknown) {
      const s = (e2 as { response?: { status?: number } })?.response?.status;
      setErr(s === 400 || s === 404 || s === 422 ? t.badToken : t.err);
    } finally {
      setBusy(false);
    }
  }

  const isConfirm = !!token;

  return (
    <div className="w-full max-w-sm mx-auto bg-white rounded-2xl shadow-sm border border-slate-100 p-7">
      <h1 className="text-xl font-bold text-slate-900">{isConfirm ? t.cfmTitle : t.reqTitle}</h1>
      <p className="text-sm text-slate-500 mt-1.5 mb-5">{isConfirm ? t.cfmSub : t.reqSub}</p>

      {done ? (
        <div className="space-y-4">
          <p className="text-sm text-slate-700 bg-green-soft border border-success/30 rounded-lg px-4 py-3">
            {isConfirm ? t.resetOk : t.sent}
          </p>
          <Link href="/login" className="block text-center text-sm font-semibold text-[#2563EB] hover:underline">
            {t.back}
          </Link>
        </div>
      ) : isConfirm ? (
        <form onSubmit={onConfirm} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">{t.newPw}</label>
            <input type="password" autoComplete="new-password" placeholder="••••••••"
              value={pw} onChange={(e) => setPw(e.target.value)} className={INPUT} required />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">{t.confirmPw}</label>
            <input type="password" autoComplete="new-password" placeholder="••••••••"
              value={pw2} onChange={(e) => setPw2(e.target.value)} className={INPUT} required />
          </div>
          {err && <p className="text-xs text-danger">{err}</p>}
          <button type="submit" disabled={busy}
            className="w-full h-11 rounded-lg bg-[#2563EB] text-white text-sm font-semibold hover:opacity-90 disabled:opacity-50">
            {busy ? t.resetting : t.reset}
          </button>
          <Link href="/login" className="block text-center text-sm text-slate-500 hover:underline">{t.back}</Link>
        </form>
      ) : (
        <form onSubmit={onRequest} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">{t.email}</label>
            <input type="email" autoComplete="email" placeholder="you@farm.com"
              value={email} onChange={(e) => setEmail(e.target.value)} className={INPUT} required />
          </div>
          {err && <p className="text-xs text-danger">{err}</p>}
          <button type="submit" disabled={busy}
            className="w-full h-11 rounded-lg bg-[#2563EB] text-white text-sm font-semibold hover:opacity-90 disabled:opacity-50">
            {busy ? t.sending : t.send}
          </button>
          <Link href="/login" className="block text-center text-sm text-slate-500 hover:underline">{t.back}</Link>
        </form>
      )}
    </div>
  );
}
