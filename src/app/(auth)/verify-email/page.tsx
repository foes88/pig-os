export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0F1B2D] px-6">
      <div className="bg-white rounded-2xl shadow-2xl p-10 w-full max-w-md text-center">
        <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mx-auto mb-6">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 5L2 7"/>
          </svg>
        </div>
        <h1 className="text-2xl font-extrabold text-[#0F172A] tracking-tight mb-2">이메일을 확인하세요</h1>
        <p className="text-sm text-gray-500 leading-relaxed mb-1">가입하신 이메일로 인증 링크를 보냈습니다.</p>
        <p className="text-xs text-gray-400 mb-8">링크를 클릭하면 가입이 완료됩니다.</p>
        <button className="w-full bg-[#0D1B3E] text-white py-3.5 rounded-xl text-sm font-bold hover:opacity-90 transition">
          이메일 앱 열기
        </button>
        <p className="mt-5 text-xs text-gray-400">
          이메일을 못 받으셨나요?{" "}
          <span className="text-blue-600 font-semibold cursor-pointer">다시 보내기</span>
          {" · "}
          <span className="text-gray-400 cursor-pointer">주소 변경</span>
        </p>
      </div>
    </div>
  );
}
