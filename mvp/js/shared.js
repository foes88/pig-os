/* ============================================================
   PigOS — Shared JS (sidebar, i18n, unit system)
   ============================================================ */

// ── Current Settings (persisted in localStorage) ──
var APP = {
  lang: localStorage.getItem('ppc_lang') || 'en',
  units: localStorage.getItem('ppc_units') || 'METRIC',
  farm: 'FARM-KR-001'
};

// ── Language Packs ──
var LANG = {
  en: {
    todays_work: "Today's Work",
    dashboard: "Dashboard",
    pipeline_view: "Pipeline View",
    breeding: "Breeding",
    gestation: "Gestation",
    farrowing: "Farrowing",
    lactation: "Lactation",
    weaning: "Weaning",
    sow_mgmt: "Sow Management",
    fattening: "Fattening",
    feed_cost: "Feed & Cost",
    health: "Health",
    shipment: "Shipment",
    ai_insights: "AI Insights",
    predictions: "Predictions",
    anomaly: "Anomaly Detection",
    reports: "Reports",
    settings: "Settings",
    record_event: "+ Record Event",
    breeding_due: "Breeding Due",
    preg_check: "Preg Check",
    farrowing_due: "Farrowing Due",
    weaning_due: "Weaning Due",
    health_alerts: "Health Alerts",
    quick_actions: "Quick Actions",
    alerts: "Alerts",
    herd_summary: "Herd Summary",
    todays_tasks: "Today's Tasks",
    gestating: "Gestating",
    lactating: "Lactating",
    open_npd: "Open/NPD",
    finisher: "Finisher",
    overdue: "Overdue",
    tomorrow: "Tomorrow",
    language: "Language",
    unit_system: "Unit System",
    metric: "Metric (kg, °C)",
    imperial: "Imperial (lb, °F)",
    weight_unit: "kg",
    temp_unit: "°C"
  },
  ko: {
    todays_work: "오늘의 업무",
    dashboard: "대시보드",
    pipeline_view: "파이프라인",
    breeding: "교배",
    gestation: "임신",
    farrowing: "분만",
    lactation: "포유",
    weaning: "이유",
    sow_mgmt: "모돈 관리",
    fattening: "비육",
    feed_cost: "사료·원가",
    health: "건강·방역",
    shipment: "출하",
    ai_insights: "AI 인사이트",
    predictions: "예측",
    anomaly: "이상 탐지",
    reports: "보고서",
    settings: "설정",
    record_event: "+ 이벤트 기록",
    breeding_due: "교배 예정",
    preg_check: "임신 확인",
    farrowing_due: "분만 예정",
    weaning_due: "이유 예정",
    health_alerts: "건강 알림",
    quick_actions: "빠른 기록",
    alerts: "알림",
    herd_summary: "돈군 현황",
    todays_tasks: "오늘의 할 일",
    gestating: "임신 중",
    lactating: "포유 중",
    open_npd: "비생산/NPD",
    finisher: "비육 출하 대기",
    overdue: "지연",
    tomorrow: "내일",
    language: "언어",
    unit_system: "단위 체계",
    metric: "미터법 (kg, °C)",
    imperial: "야드법 (lb, °F)",
    weight_unit: "kg",
    temp_unit: "°C"
  },
  vi: {
    todays_work: "Công việc hôm nay",
    dashboard: "Bảng điều khiển",
    pipeline_view: "Quy trình",
    breeding: "Phối giống",
    gestation: "Mang thai",
    farrowing: "Đẻ",
    lactation: "Cho con bú",
    weaning: "Cai sữa",
    sow_mgmt: "Quản lý nái",
    fattening: "Vỗ béo",
    feed_cost: "Thức ăn & Chi phí",
    health: "Sức khỏe",
    shipment: "Xuất bán",
    ai_insights: "AI phân tích",
    predictions: "Dự đoán",
    anomaly: "Phát hiện bất thường",
    reports: "Báo cáo",
    settings: "Cài đặt",
    record_event: "+ Ghi sự kiện",
    breeding_due: "Phối giống",
    preg_check: "Kiểm tra thai",
    farrowing_due: "Sắp đẻ",
    weaning_due: "Cai sữa",
    health_alerts: "Cảnh báo",
    quick_actions: "Thao tác nhanh",
    alerts: "Cảnh báo",
    herd_summary: "Tổng quan đàn",
    todays_tasks: "Việc hôm nay",
    gestating: "Mang thai",
    lactating: "Cho bú",
    open_npd: "Chờ/NPD",
    finisher: "Xuất chuồng",
    overdue: "Quá hạn",
    tomorrow: "Ngày mai",
    language: "Ngôn ngữ",
    unit_system: "Hệ đơn vị",
    metric: "Mét (kg, °C)",
    imperial: "Anh (lb, °F)",
    weight_unit: "kg",
    temp_unit: "°C"
  }
};

// ── Translation helper ──
function t(key) {
  return (LANG[APP.lang] && LANG[APP.lang][key]) || (LANG.en[key]) || key;
}

// ── Unit conversion ──
function toWeight(kg) {
  if (APP.units === 'IMPERIAL') return (kg * 2.20462).toFixed(1);
  return kg;
}
function weightUnit() {
  return APP.units === 'IMPERIAL' ? 'lb' : 'kg';
}
function toTemp(celsius) {
  if (APP.units === 'IMPERIAL') return (celsius * 9/5 + 32).toFixed(1);
  return celsius;
}
function tempUnit() {
  return APP.units === 'IMPERIAL' ? '°F' : '°C';
}

// ── Set language ──
function setLang(lang) {
  APP.lang = lang;
  localStorage.setItem('ppc_lang', lang);
  applyTranslations();
  updateDropdownUI();
}

// ── Set unit system ──
function setUnits(system) {
  APP.units = system;
  localStorage.setItem('ppc_units', system);
  updateDropdownUI();
  // Pages can listen for this
  document.dispatchEvent(new CustomEvent('unitsChanged', { detail: { system: system } }));
}

// ── Apply translations to [data-i18n] elements ──
function applyTranslations() {
  document.querySelectorAll('[data-i18n]').forEach(function(el) {
    var key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });
}

// ── Settings Dropdown Toggle ──
function toggleSettingsDropdown(e) {
  e.stopPropagation();
  var dd = document.getElementById('settingsDropdown');
  if (dd) dd.classList.toggle('open');
}

// Close dropdown on outside click
document.addEventListener('click', function() {
  var dd = document.getElementById('settingsDropdown');
  if (dd) dd.classList.remove('open');
});

// ── Update dropdown active states ──
function updateDropdownUI() {
  document.querySelectorAll('.lang-option').forEach(function(el) {
    el.classList.toggle('active', el.dataset.lang === APP.lang);
    var check = el.querySelector('.check');
    if (check) check.style.display = el.dataset.lang === APP.lang ? '' : 'none';
  });
  document.querySelectorAll('.unit-option').forEach(function(el) {
    el.classList.toggle('active', el.dataset.units === APP.units);
    var check = el.querySelector('.check');
    if (check) check.style.display = el.dataset.units === APP.units ? '' : 'none';
  });
  // Update trigger label
  var trigger = document.querySelector('.dd-trigger .lang-label');
  if (trigger) {
    var labels = { en: '🌐 EN', ko: '🌐 KO', vi: '🌐 VI' };
    trigger.textContent = labels[APP.lang] || '🌐 EN';
  }
}

// ── Init on page load ──
document.addEventListener('DOMContentLoaded', function() {
  applyTranslations();
  updateDropdownUI();
});
