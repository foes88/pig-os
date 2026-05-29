export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0F1B2D]">
      <div className="w-full max-w-[400px] px-4">
        {/* Logo */}
        <div className="text-center mb-8">
          <span className="text-3xl font-extrabold tracking-tight text-white">
            Pig<span className="text-[#2563EB]">OS</span>
          </span>
          <p className="text-sm text-slate-400 mt-1">Farm Operating System</p>
        </div>
        {children}
      </div>
    </div>
  );
}
