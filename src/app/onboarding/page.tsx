"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { authApi } from "@/lib/api/endpoints/auth";
import { useAuthStore } from "@/store/auth.store";
import { track, identifyUser } from "@/lib/analytics";

// 예약어 아이디 차단(백엔드 auth.py와 동일 규칙) — 사칭 방지, 즉시 피드백용.
const RESERVED_UN = /^(admin|administrator|root|superuser|superadmin|super_admin|system|sysadmin|support|helpdesk|info|contact|moderator|mod|staff|operator|owner|master|official|security|billing|api|www|pigos|pigplan|wiselake|null|undefined)$/;
function isReservedUsername(u: string): boolean {
  const norm = u.trim().toLowerCase().replace(/0/g, "o").replace(/1/g, "i").replace(/3/g, "e").replace(/4/g, "a").replace(/5/g, "s").replace(/@/g, "a").replace(/\$/g, "s");
  return RESERVED_UN.test(norm) || norm.startsWith("admin") || /administrator|pigos|wiselake|superadmin/.test(norm);
}
import type { OnboardingRequest } from "@/types/api.types";

const COUNTRIES = [
  { value: "KR", label: "South Korea" },
  { value: "US", label: "United States" },
  { value: "CN", label: "China" },
  { value: "VN", label: "Vietnam" },
  { value: "TH", label: "Thailand" },
  { value: "PH", label: "Philippines" },
  { value: "BR", label: "Brazil" },
  { value: "MX", label: "Mexico" },
];

// 온보딩은 pre-auth — 한국어는 관리자 전용이라 노출 안 함(공개 7개어 + 미지정 en 폴백).
type OLang = "en" | "zh" | "es" | "vi" | "th" | "pt" | "ru";
const OT: Record<OLang, Record<string, string>> = {
  en: { s0: "Farm Info", s1: "Account", s2: "Confirm", t0: "Farm information", d0: "Tell us about your farm operation", org: "Organization / Company *", farm: "Farm name *", country: "Country *", ftype: "Farm type", sows: "Sow count", t1: "Create your account", d1: "You'll use this to sign in to PigOS", name: "Full name *", username: "Username (ID) *", email: "Email address *", pw: "Password * (min. 8 characters)", cpw: "Confirm password *", mismatch: "Passwords do not match", t2: "Confirm & start", d2: "Review your details before creating your account", rOrg: "Organization", rFarm: "Farm", rCountry: "Country", rFtype: "Farm type", rSows: "Sow count", rName: "Name", rEmail: "Email", head: "head", free: "Free to start. No credit card required.", back: "Back", cont: "Continue", get: "Get started free", creating: "Creating account…", have: "Already have an account?", signin: "Sign in", sowFarm: "Sow farm", f2f: "Farrow-to-finish", nursery: "Nursery", finisher: "Finisher" },
  zh: { s0: "农场信息", s1: "账户", s2: "确认", t0: "农场信息", d0: "请介绍您的养殖场", org: "机构 / 公司 *", farm: "农场名称 *", country: "国家 *", ftype: "农场类型", sows: "母猪数", t1: "创建账户", d1: "用于登录 PigOS", name: "姓名 *", username: "账号 *", email: "邮箱 *", pw: "密码 *（至少8位）", cpw: "确认密码 *", mismatch: "密码不一致", t2: "确认并开始", d2: "创建账户前请核对信息", rOrg: "机构", rFarm: "农场", rCountry: "国家", rFtype: "农场类型", rSows: "母猪数", rName: "姓名", rEmail: "邮箱", head: "头", free: "免费开始，无需信用卡。", back: "返回", cont: "继续", get: "免费开始", creating: "创建中…", have: "已有账户？", signin: "登录", sowFarm: "母猪场", f2f: "自繁自养", nursery: "保育场", finisher: "育肥场" },
  es: { s0: "Granja", s1: "Cuenta", s2: "Confirmar", t0: "Información de la granja", d0: "Cuéntanos sobre tu operación", org: "Organización / Empresa *", farm: "Nombre de la granja *", country: "País *", ftype: "Tipo de granja", sows: "N.º de cerdas", t1: "Crea tu cuenta", d1: "La usarás para entrar en PigOS", name: "Nombre completo *", username: "Usuario (ID) *", email: "Correo electrónico *", pw: "Contraseña * (mín. 8 caracteres)", cpw: "Confirmar contraseña *", mismatch: "Las contraseñas no coinciden", t2: "Confirmar e iniciar", d2: "Revisa tus datos antes de crear la cuenta", rOrg: "Organización", rFarm: "Granja", rCountry: "País", rFtype: "Tipo de granja", rSows: "N.º de cerdas", rName: "Nombre", rEmail: "Correo", head: "cabezas", free: "Gratis para empezar. Sin tarjeta.", back: "Atrás", cont: "Continuar", get: "Empezar gratis", creating: "Creando cuenta…", have: "¿Ya tienes cuenta?", signin: "Iniciar sesión", sowFarm: "Granja de cerdas", f2f: "Ciclo completo", nursery: "Destete", finisher: "Engorde" },
  vi: { s0: "Trang trại", s1: "Tài khoản", s2: "Xác nhận", t0: "Thông tin trang trại", d0: "Cho chúng tôi biết về trang trại của bạn", org: "Tổ chức / Công ty *", farm: "Tên trang trại *", country: "Quốc gia *", ftype: "Loại trang trại", sows: "Số nái", t1: "Tạo tài khoản", d1: "Dùng để đăng nhập PigOS", name: "Họ tên *", username: "Tên đăng nhập (ID) *", email: "Email *", pw: "Mật khẩu * (tối thiểu 8 ký tự)", cpw: "Xác nhận mật khẩu *", mismatch: "Mật khẩu không khớp", t2: "Xác nhận & bắt đầu", d2: "Kiểm tra thông tin trước khi tạo tài khoản", rOrg: "Tổ chức", rFarm: "Trang trại", rCountry: "Quốc gia", rFtype: "Loại trang trại", rSows: "Số nái", rName: "Họ tên", rEmail: "Email", head: "con", free: "Miễn phí để bắt đầu. Không cần thẻ.", back: "Quay lại", cont: "Tiếp tục", get: "Bắt đầu miễn phí", creating: "Đang tạo tài khoản…", have: "Đã có tài khoản?", signin: "Đăng nhập", sowFarm: "Trại nái", f2f: "Khép kín", nursery: "Cai sữa", finisher: "Vỗ béo" },
  th: { s0: "ฟาร์ม", s1: "บัญชี", s2: "ยืนยัน", t0: "ข้อมูลฟาร์ม", d0: "บอกเราเกี่ยวกับฟาร์มของคุณ", org: "องค์กร / บริษัท *", farm: "ชื่อฟาร์ม *", country: "ประเทศ *", ftype: "ประเภทฟาร์ม", sows: "จำนวนแม่สุกร", t1: "สร้างบัญชี", d1: "ใช้เข้าสู่ระบบ PigOS", name: "ชื่อ-นามสกุล *", username: "ชื่อผู้ใช้ (ID) *", email: "อีเมล *", pw: "รหัสผ่าน * (อย่างน้อย 8 ตัว)", cpw: "ยืนยันรหัสผ่าน *", mismatch: "รหัสผ่านไม่ตรงกัน", t2: "ยืนยันและเริ่ม", d2: "ตรวจสอบข้อมูลก่อนสร้างบัญชี", rOrg: "องค์กร", rFarm: "ฟาร์ม", rCountry: "ประเทศ", rFtype: "ประเภทฟาร์ม", rSows: "จำนวนแม่สุกร", rName: "ชื่อ", rEmail: "อีเมล", head: "ตัว", free: "เริ่มฟรี ไม่ต้องใช้บัตร", back: "ย้อนกลับ", cont: "ต่อไป", get: "เริ่มฟรี", creating: "กำลังสร้างบัญชี…", have: "มีบัญชีแล้ว?", signin: "เข้าสู่ระบบ", sowFarm: "ฟาร์มแม่สุกร", f2f: "ครบวงจร", nursery: "อนุบาล", finisher: "ขุน" },
  pt: { s0: "Granja", s1: "Conta", s2: "Confirmar", t0: "Informações da granja", d0: "Conte-nos sobre sua operação", org: "Organização / Empresa *", farm: "Nome da granja *", country: "País *", ftype: "Tipo de granja", sows: "N.º de matrizes", t1: "Crie sua conta", d1: "Você usará para entrar no PigOS", name: "Nome completo *", username: "Usuário (ID) *", email: "E-mail *", pw: "Senha * (mín. 8 caracteres)", cpw: "Confirmar senha *", mismatch: "As senhas não coincidem", t2: "Confirmar e começar", d2: "Revise seus dados antes de criar a conta", rOrg: "Organização", rFarm: "Granja", rCountry: "País", rFtype: "Tipo de granja", rSows: "N.º de matrizes", rName: "Nome", rEmail: "E-mail", head: "cabeças", free: "Grátis para começar. Sem cartão.", back: "Voltar", cont: "Continuar", get: "Começar grátis", creating: "Criando conta…", have: "Já tem conta?", signin: "Entrar", sowFarm: "Granja de matrizes", f2f: "Ciclo completo", nursery: "Creche", finisher: "Terminação" },
  ru: { s0: "Ферма", s1: "Аккаунт", s2: "Подтверждение", t0: "Информация о ферме", d0: "Расскажите о вашем хозяйстве", org: "Организация / Компания *", farm: "Название фермы *", country: "Страна *", ftype: "Тип фермы", sows: "Кол-во свиноматок", t1: "Создайте аккаунт", d1: "Используйте его для входа в PigOS", name: "Полное имя *", username: "Логин (ID) *", email: "Электронная почта *", pw: "Пароль * (мин. 8 символов)", cpw: "Подтвердите пароль *", mismatch: "Пароли не совпадают", t2: "Подтвердить и начать", d2: "Проверьте данные перед созданием аккаунта", rOrg: "Организация", rFarm: "Ферма", rCountry: "Страна", rFtype: "Тип фермы", rSows: "Кол-во свиноматок", rName: "Имя", rEmail: "Почта", head: "голов", free: "Бесплатный старт. Без банковской карты.", back: "Назад", cont: "Продолжить", get: "Начать бесплатно", creating: "Создание аккаунта…", have: "Уже есть аккаунт?", signin: "Войти", sowFarm: "Ферма свиноматок", f2f: "Полный цикл", nursery: "Доращивание", finisher: "Откорм" },
};

type Form = OnboardingRequest;

export default function OnboardingPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<Form>({
    org_name: "",
    country: "KR",
    name: "",
    username: "",
    email: "",
    password: "",
    farm_name: "",
    farm_type: "FARROW_TO_FINISH",
    sow_count: 100,
    timezone: "Asia/Seoul",
  });
  const [confirmPw, setConfirmPw] = useState("");
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof Form>(k: K, v: Form[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  // pre-auth 로케일: NEXT_LOCALE 쿠키(한국어는 관리자전용 → en으로). 6개 공개어.
  const [lang, setLang] = useState<OLang>("en");
  useEffect(() => {
    const m = document.cookie.match(/(?:^|;\s*)NEXT_LOCALE=([^;]+)/);
    const c = m?.[1];
    if (c && c !== "ko" && c in OT) setLang(c as OLang);
  }, []);
  const t = OT[lang];
  const STEPS = [t.s0, t.s1, t.s2];
  const FARM_TYPES = [
    { value: "SOW_FARM", label: t.sowFarm },
    { value: "FARROW_TO_FINISH", label: t.f2f },
    { value: "NURSERY", label: t.nursery },
    { value: "FINISHER", label: t.finisher },
  ];

  const mutation = useMutation({
    mutationFn: () => authApi.onboard({ ...form, language: lang }),  // M3: 감지된 로케일 전송
    onSuccess: (data) => {
      setAuth(
        { id: data.user_id, username: form.username, email: form.email, name: form.name, role: "FARM_OWNER", farm_ids: [data.farm_id] },
        data.access_token,
        data.refresh_token,
        data.farm_id,
      );
      document.cookie = `pigos_session=1; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
      identifyUser(data.user_id, { country: form.country });
      track("signup", { country: form.country });
      router.replace("/");
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Something went wrong. Please try again.");
    },
  });

  const canProceed = () => {
    if (step === 0) return form.org_name.trim() && form.farm_name.trim() && form.country;
    if (step === 1) return form.name.trim() && /^[a-zA-Z0-9_.-]{3,50}$/.test(form.username) && form.email.trim() && form.password.length >= 8 && form.password === confirmPw;
    return true;
  };

  const next = () => {
    setError(null);
    if (step === 1 && isReservedUsername(form.username)) {
      setError("This username is reserved and cannot be used.");
      return;
    }
    if (step < 2) setStep((s) => s + 1);
    else mutation.mutate();
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-[520px]">

        {/* Logo */}
        <div className="flex justify-center mb-8">
          <Image
            src="/logos/pigos-logo-horizontal-light.svg"
            alt="PigOS"
            width={140}
            height={53}
            className="object-contain"
            priority
          />
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-0 mb-8">
          {STEPS.map((label, i) => (
            <div key={i} className="flex items-center">
              <div className="flex flex-col items-center gap-1.5">
                <div className={`flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold border-2 transition-all ${
                  i < step
                    ? "bg-[#2563EB] border-[#2563EB] text-white"
                    : i === step
                    ? "bg-white border-[#2563EB] text-[#2563EB]"
                    : "bg-white border-slate-200 text-slate-400"
                }`}>
                  {i < step ? (
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 6 9 17l-5-5"/>
                    </svg>
                  ) : (
                    i + 1
                  )}
                </div>
                <span className={`text-xs ${i === step ? "text-slate-700 font-medium" : "text-slate-400"}`}>
                  {label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={`h-px w-16 mx-3 mb-5 ${i < step ? "bg-[#2563EB]" : "bg-slate-200"}`} />
              )}
            </div>
          ))}
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
          {step === 0 && (
            <div className="space-y-4">
              <div className="mb-6">
                <h2 className="text-lg font-bold text-slate-900">{t.t0}</h2>
                <p className="text-sm text-slate-500 mt-0.5">{t.d0}</p>
              </div>
              <Field label={t.org}>
                <input value={form.org_name} onChange={(e) => set("org_name", e.target.value)} data-testid="onb-org-name"
                  placeholder="e.g. WiseLake Farm Co." className="fin" />
              </Field>
              <Field label={t.farm}>
                <input value={form.farm_name} onChange={(e) => set("farm_name", e.target.value)} data-testid="onb-farm-name"
                  placeholder="e.g. Main Farm" className="fin" />
              </Field>
              <div className="grid grid-cols-2 gap-4">
                <Field label={t.country}>
                  <select value={form.country} onChange={(e) => set("country", e.target.value)} className="fin">
                    {COUNTRIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </Field>
                <Field label={t.ftype}>
                  <select value={form.farm_type} onChange={(e) => set("farm_type", e.target.value as Form["farm_type"])} className="fin">
                    {FARM_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </Field>
              </div>
              <Field label={t.sows}>
                <input type="number" min={1} value={form.sow_count ?? ""}
                  onChange={(e) => set("sow_count", Number(e.target.value))}
                  placeholder="e.g. 500" className="fin" />
              </Field>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <div className="mb-6">
                <h2 className="text-lg font-bold text-slate-900">{t.t1}</h2>
                <p className="text-sm text-slate-500 mt-0.5">{t.d1}</p>
              </div>
              <Field label={t.name}>
                <input value={form.name} onChange={(e) => set("name", e.target.value)} data-testid="onb-name"
                  placeholder="e.g. John Kim" className="fin" />
              </Field>
              <Field label={t.username}>
                <input value={form.username} onChange={(e) => set("username", e.target.value)} data-testid="onb-username"
                  placeholder="admin" autoComplete="username" className="fin" />
              </Field>
              <Field label={t.email}>
                <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} data-testid="onb-email"
                  placeholder="farmer@example.com" className="fin" />
              </Field>
              <Field label={t.pw}>
                <input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} data-testid="onb-password"
                  placeholder="••••••••" className="fin" />
              </Field>
              <Field label={t.cpw}>
                <input type="password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)} data-testid="onb-confirm"
                  placeholder="••••••••" className={`fin ${confirmPw && form.password !== confirmPw ? "!border-red-400" : ""}`} />
                {confirmPw && form.password !== confirmPw && (
                  <p className="text-xs text-danger mt-1">{t.mismatch}</p>
                )}
              </Field>
            </div>
          )}

          {step === 2 && (
            <div>
              <div className="mb-6">
                <h2 className="text-lg font-bold text-slate-900">{t.t2}</h2>
                <p className="text-sm text-slate-500 mt-0.5">{t.d2}</p>
              </div>
              <div className="rounded-xl border border-slate-200 overflow-hidden">
                {[
                  [t.rOrg, form.org_name],
                  [t.rFarm, form.farm_name],
                  [t.rCountry, COUNTRIES.find((c) => c.value === form.country)?.label ?? form.country],
                  [t.rFtype, FARM_TYPES.find((ft) => ft.value === form.farm_type)?.label ?? form.farm_type ?? ""],
                  [t.rSows, `${form.sow_count ?? "-"} ${t.head}`],
                  [t.rName, form.name],
                  [t.username, form.username],
                  [t.rEmail, form.email],
                ].map(([label, value], idx, arr) => (
                  <div key={label} className={`flex justify-between px-4 py-3 text-sm ${idx < arr.length - 1 ? "border-b border-slate-100" : ""}`}>
                    <span className="text-slate-500">{label}</span>
                    <span className="text-slate-900 font-medium">{value}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-4 flex items-center gap-1.5">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                {t.free}
              </p>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2.5 bg-red-soft border border-danger/40 rounded-lg px-4 py-3 mt-4">
              <svg className="w-4 h-4 text-danger mt-0.5 shrink-0" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <p className="text-sm text-danger">{error}</p>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            {step > 0 && (
              <button onClick={() => setStep((s) => s - 1)}
                className="flex-1 h-11 border border-slate-300 text-slate-700 rounded-lg text-sm
                  font-medium hover:bg-slate-50 transition">
                {t.back}
              </button>
            )}
            <button onClick={next} data-testid="onb-next"
              disabled={!canProceed() || mutation.isPending}
              className="flex-1 h-11 bg-[#2563EB] hover:bg-[#1D4ED8] disabled:opacity-50
                text-white font-semibold rounded-lg text-sm transition shadow-sm shadow-blue-200/60">
              {mutation.isPending ? t.creating : step === 2 ? t.get : t.cont}
            </button>
          </div>
        </div>

        <p className="text-center text-sm text-slate-500 mt-5">
          {t.have}{" "}
          <a href="/login" className="text-[#2563EB] hover:underline font-medium">{t.signin}</a>
        </p>
        <p className="text-center text-xs text-slate-400 mt-3">© 2026 WiseLake Inc.</p>
      </div>

      <style>{`
        .fin {
          width: 100%;
          height: 44px;
          padding: 0 0.875rem;
          border-radius: 0.5rem;
          background: #fff;
          border: 1px solid #CBD5E1;
          color: #0f172a;
          font-size: 0.875rem;
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
        }
        .fin:focus {
          border-color: #2563EB;
          box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
        }
        .fin::placeholder { color: #94a3b8; }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1.5">{label}</label>
      {children}
    </div>
  );
}
