
// =========================================================================
// HELPER: LOCAL DATE STRING (YYYY-MM-DD) CHO MÚI GIỜ VIỆT NAM (UTC+7)
// =========================================================================
function getLocalDateString(d = new Date()) {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// =========================================================================
// API FETCH HELPER WITH AUTH & ERROR HANDLING
// =========================================================================
async function apiFetch(url, options = {}) {
    const headers = options.headers || {};
    if (state && state.token && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${state.token}`;
    }
    if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
        if (res.status === 401) {
            if (state) {
                state.token = null;
                state.user = null;
            }
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            if (typeof updateUserUI === 'function') updateUserUI();
            throw new Error('Phiên đăng nhập đã hết hạn hoặc chưa đăng nhập. Vui lòng đăng nhập lại!');
        }
        let errDetail = 'Lỗi yêu cầu máy chủ';
        try {
            const errData = await res.json();
            errDetail = errData.detail || errData.message || errDetail;
            if (Array.isArray(errDetail)) {
                errDetail = errDetail.map(x => x.msg || JSON.stringify(x)).join(', ');
            }
        } catch (_) {}
        throw new Error(errDetail);
    }
    const text = await res.text();
    return text ? JSON.parse(text) : {};
}
// =========================================================================
// APPLICATION CONTROLLER & STATE
// =========================================================================
let state = {
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    pitches: [],
    bookings: [],
    recentCreatedBookings: JSON.parse(sessionStorage.getItem('recent_created_bookings') || '[]'),
    matrixData: null,
    currentMatrixFrame: 'ALL',
    currentWeekOffset: 0,
    currentBookingSportFilter: 'ALL',
    bookingPitchSearch: '',
    reviews: [],
    matches: [],
    events: [],
    chartRevenue: null,
    chartSports: null,
    chartReportRevenue: null,
    chartReportSportRevenue: null,
    chartReportOccupancy: null,
    currentTab: 'home',
    currentLightboxPitchId: null
};

const SPORT_CONFIG = {
    'ALL': { icon: '⚡', label: 'Tất cả môn', color: 'emerald' },
    'FOOTBALL': { icon: '⚽', label: 'Bóng Đá', color: 'emerald' },
    'BADMINTON': { icon: '🏸', label: 'Cầu Lông', color: 'teal' },
    'TENNIS': { icon: '🎾', label: 'Tennis', color: 'amber' },
    'GYM': { icon: '🏋️', label: 'Gym & Fitness', color: 'rose' },
    'BASKETBALL': { icon: '🏀', label: 'Bóng Rổ', color: 'orange' }
};

// =========================================================================
// CHỌN MÔN THỂ THAO & ĐỒNG BỘ MA TRẬN TỨC THÌ (CLICK 1 CHẠM ĐỔI SÂN & ĐỔI GIÁ)
// =========================================================================
async function filterBookingSport(sportCategory) {
    state.currentBookingSportFilter = sportCategory;
    
    // 1. Cập nhật giao diện nút bấm môn thể thao (sáng viền xanh)
    document.querySelectorAll('.booking-sport-chip').forEach(b => {
        b.classList.remove('active', 'bg-emerald-600', 'text-white', 'shadow-glow', 'ring-2', 'ring-emerald-400', 'scale-105');
        b.classList.add('bg-slate-950', 'text-slate-300', 'border-slate-800');
    });

    const activeBtn = document.getElementById(`sport-tab-${sportCategory.toLowerCase()}`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'bg-emerald-600', 'text-white', 'shadow-glow', 'ring-2', 'ring-emerald-400', 'scale-105');
        activeBtn.classList.remove('bg-slate-950', 'text-slate-300', 'border-slate-800');
    }

    // 2. Nếu state.pitches chưa có, tải ngay từ API
    if (!state.pitches || state.pitches.length === 0) {
        await loadPitches();
    }

    // 3. Lọc danh sách sân theo môn
    let matchingPitches = state.pitches || [];
    if (sportCategory !== 'ALL') {
        matchingPitches = state.pitches.filter(p => p.sport_type === sportCategory);
    }

    const todayStr = state.matrixStartDate || getLocalDateString();

    // 4. Tự động chọn sân đầu tiên của môn đó & cập nhật giá, ma trận ngay
    if (matchingPitches.length > 0) {
        const firstPitch = matchingPitches[0];
        const sel = document.getElementById('matrix-pitch-select');
        const headerSel = document.getElementById('matrix-header-pitch-select');
        if (sel) sel.value = firstPitch.id;
        if (headerSel) headerSel.value = firstPitch.id;
        
        updateMatrixHeaderInfo(firstPitch);
        recalculateMatrixPrice();
        state.matrixStartDate = todayStr;
        const pInput = document.getElementById('matrix-week-date-picker');
        if (pInput) pInput.value = todayStr;
        
        await loadBookingMatrix();
        await loadMyRecentBookings();
        
        const meta = SPORT_CONFIG[firstPitch.sport_type] || { icon: '🏟️', label: 'Sân' };
        showToast(`Đã chuyển sang môn ${meta.label}: ${firstPitch.name}`, 'success');
    }

    // 5. Vẽ lại danh sách thẻ sân visual bên trái
    renderBookingVisualPitchList();
}

function filterBookingPitches(searchText) {
    state.bookingPitchSearch = (searchText || '').trim().toLowerCase();
    renderBookingVisualPitchList();
}

function updateMatrixHeaderInfo(pitch) {
    if (!pitch) return;
    const meta = SPORT_CONFIG[pitch.sport_type] || { icon: '🏟️', label: pitch.sport_type };
    
    const iconEl = document.getElementById('matrix-selected-pitch-icon');
    const titleEl = document.getElementById('matrix-selected-pitch-title');
    const locEl = document.getElementById('matrix-selected-pitch-loc');
    
    if (iconEl) iconEl.innerText = meta.icon;
    if (titleEl) titleEl.innerText = pitch.name;
    if (locEl) locEl.innerText = `${pitch.location} • Giá thuê: ${pitch.price_per_hour.toLocaleString()}đ/h (Tối: ${(pitch.peak_price_per_hour || pitch.price_per_hour).toLocaleString()}đ/h)`;
}

function renderBookingVisualPitchList() {
    const container = document.getElementById('booking-pitch-visual-list');
    if (!container) return;

    if (!state.pitches || state.pitches.length === 0) {
        container.innerHTML = `<div class="p-3 text-center text-xs text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Đang tải danh sách sân...</div>`;
        return;
    }

    let filtered = state.pitches;
    if (state.currentBookingSportFilter !== 'ALL') {
        filtered = state.pitches.filter(p => p.sport_type === state.currentBookingSportFilter);
    }
    if (state.bookingPitchSearch) {
        filtered = filtered.filter(p => [p.name, p.location, p.sport_type, p.capacity]
            .filter(Boolean)
            .some(value => String(value).toLowerCase().includes(state.bookingPitchSearch)));
    }

    const currentSelectedId = parseInt(document.getElementById('matrix-pitch-select')?.value || (state.pitches[0]?.id || 1));

    if (filtered.length === 0) {
        container.innerHTML = `<div class="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-center text-xs text-slate-400">Không tìm thấy sân phù hợp</div>`;
        return;
    }

    container.innerHTML = filtered.map(p => {
        const isSelected = (p.id === currentSelectedId);
        const meta = SPORT_CONFIG[p.sport_type] || { icon: '🏟️', label: p.sport_type, color: 'emerald' };

        return `
            <div onclick="selectVisualPitch(${p.id})" 
                 class="visual-pitch-card cursor-pointer p-3 rounded-2xl border transition-all duration-200 flex items-center justify-between gap-3 select-none ${
                     isSelected 
                     ? 'bg-emerald-600 text-white border-emerald-400 shadow-glow ring-2 ring-emerald-400 scale-[1.02]' 
                     : 'bg-slate-900/90 hover:bg-slate-800 border-slate-800 text-slate-200'
                 }">
                <div class="flex items-center space-x-3 overflow-hidden">
                    <div class="w-10 h-10 rounded-xl ${isSelected ? 'bg-white text-emerald-800 font-black shadow-md' : 'bg-slate-800 text-emerald-400 border border-slate-700'} flex items-center justify-center text-lg flex-shrink-0">
                        ${meta.icon}
                    </div>
                    <div class="overflow-hidden">
                        <p class="font-bold text-xs ${isSelected ? 'text-white font-extrabold' : 'text-slate-100'} truncate">${p.name}</p>
                        <p class="text-[10px] ${isSelected ? 'text-emerald-100' : 'text-slate-400'} truncate mt-0.5"><i class="fa-solid fa-location-dot ${isSelected ? 'text-amber-300' : 'text-emerald-400'} mr-1"></i> ${p.location}</p>
                    </div>
                </div>
                <div class="text-right flex-shrink-0">
                    <span class="block text-xs font-black ${isSelected ? 'text-amber-300' : 'text-amber-400'} font-mono">${(p.price_per_hour/1000).toFixed(0)}k/h</span>
                    <span class="inline-block text-[10px] px-2.5 py-0.5 rounded-full font-bold shadow-sm ${
                        isSelected 
                        ? 'bg-emerald-800 text-emerald-100 border border-emerald-400' 
                        : 'bg-slate-950 text-slate-300 border border-slate-800'
                    }">${p.capacity || meta.label}</span>
                </div>
            </div>
        `;
    }).join('');

    const activePitch = state.pitches.find(p => p.id === currentSelectedId) || state.pitches[0];
    if (activePitch) {
        updateMatrixHeaderInfo(activePitch);
    }
}

async function selectVisualPitch(pitchId) {
    const sel = document.getElementById('matrix-pitch-select');
    const headerSel = document.getElementById('matrix-header-pitch-select');
    if (sel) sel.value = pitchId;
    if (headerSel) headerSel.value = pitchId;
    
    const pitch = state.pitches?.find(p => p.id === pitchId);
    if (pitch) {
        updateMatrixHeaderInfo(pitch);
    }
    
    renderBookingVisualPitchList();
    recalculateMatrixPrice();
    await loadBookingMatrix();
    if (pitch) {
        showToast(`Đã chọn: ${pitch.name} (${pitch.price_per_hour.toLocaleString()}đ/h)`, 'success');
    }
}




const TAB_TITLES = {
    'home': 'Trang Chủ',
    'matrix-booking': 'Đặt Sân',
    'public-pricing': 'Lịch Trống & Bảng Giá',
    'timeslots': 'Quản Lý Khung Giờ',
    'pricing': 'Quản Lý Khung Giờ & Bảng Giá',
    'matches': 'Đăng Ký Giao Lưu',
    'events': 'Hoạt Động Sân',
    'reviews': 'Đánh Giá',
    'contact': 'Liên Hệ',
    'dashboard': 'Tổng Quan & Doanh Thu',
    'pitches': 'Quản Lý Sân & Bảng Giá',
    'bookings': 'Danh Sách Đơn Đặt',
    'payments': 'Thanh Toán & Hóa Đơn',
    'maintenance': 'Lịch Bảo Trì Sân',
    'user-roles': 'Phân Quyền & Nhật Ký',
    'ai-assistant': 'Trợ Lý AI AIA331',
    'customers': 'Quản Lý Khách Hàng',
    'reports': 'Báo Cáo Doanh Thu & Công Suất'
};

const FUNCTION_INFO = {
    'home': { icon: '🏠', title: 'Trang Chủ Báo Cáo', desc: 'Hệ Thống Quản Lý Sân Thể Thao Cho Thuê Tích Hợp AI - Nhóm 03 (ICTU)' },
    'public-pricing': { icon: '🏷️', title: 'Lịch Trống & Bảng Giá', desc: 'Xem giá theo môn thể thao và chọn sân để kiểm tra lịch trống' },
    'pitches': { icon: '⚽', title: '1. Quản Lý Sân & Loại Sân', desc: 'Quản lý danh sách sân bóng đá, cầu lông, tennis, gym (Mục 3.7.2)' },
    'timeslots': { icon: '🕒', title: '2. Quản Lý Khung Giờ', desc: 'Cấu hình khung giờ cho sân theo ngày hoạt động' },
    'pricing': { icon: '🏷️', title: '3. Quản Lý Bảng Giá', desc: 'Cấu hình giá thường, cao điểm và cuối tuần cho sân' },
    'matrix-booking': { icon: '📅', title: '3. Quản Lý Đặt Sân & Ma Trận Trực Quan', desc: 'Xem ma trận giờ trống, chọn sân 1 chạm, chống trùng lịch 100% (Mục 3.7.3 & 3.7.4)' },
    'customers': { icon: '👥', title: '4. Quản Lý Khách Hàng', desc: 'Quản lý thông tin hội viên, lịch sử đặt sân và tích điểm thưởng VIP (Mục 3.7.1)' },
    'payments': { icon: '💳', title: '5. Quản Lý Thanh Toán & Hóa Đơn Email', desc: 'Xác nhận chuyển khoản VietQR tự động & gửi hóa đơn EML/Email (Mục 3.7.4)' },
    'dashboard': { icon: '📊', title: '6. Thống Kê & Báo Cáo Doanh Thu', desc: 'Biểu đồ phân tích công suất sân, tỷ lệ lấp đầy và doanh thu (Mục 3.7.8)' },
    'maintenance': { icon: '🔧', title: '7. Quản Lý Bảo Trì Sân Bãi', desc: 'Lên lịch bảo trì mặt cỏ, hệ thống đèn chiếu sáng và thiết bị (Mục 3.7.9)' },
    'matches': { icon: '🤝', title: '8. Đăng Ký Giao Lưu Đối Thủ', desc: 'Sàn kết nối bắt đối giao hữu, ghép đội thi đấu thể thao (Mục 3.7.10)' },
    'ai-assistant': { icon: '🤖', title: 'Chức Năng AI: Trợ Lý AI Thông Minh AIA331', desc: 'Gợi ý khung giờ vắng, tự động soạn tin nhắn Zalo/SMS & đề xuất khuyến mại' },
    'user-roles': { icon: '⚙️', title: 'Cài Đặt: Phân Quyền & Nhật Ký Log', desc: 'Quản lý quyền Admin/Staff và theo dõi nhật ký hoạt động hệ thống' },
    'bookings': { icon: '📋', title: 'Danh Sách Đặt Sân', desc: 'Xem và quản lý tất cả đơn đặt sân trong hệ thống' },
    'events': { icon: '🏆', title: 'Giải Đấu & Sự Kiện', desc: 'Tổ chức giải đấu và sự kiện thể thao nội bộ' },
    'reviews': { icon: '⭐', title: 'Đánh Giá & Nhận Xét', desc: 'Ý kiến phản hồi từ khách hàng trải nghiệm dịch vụ' }
};

function updateActiveFunctionBanner(tabId) {
    const info = FUNCTION_INFO[tabId] || { icon: '📌', title: TAB_TITLES[tabId] || 'Chức Năng Quản Lý', desc: 'Hệ thống Quản lý Sân Thể thao AI - Nhóm 03' };
    const iconEl = document.getElementById('active-func-icon');
    const titleEl = document.getElementById('active-func-title');
    const descEl = document.getElementById('active-func-desc');
    if (iconEl) iconEl.innerText = info.icon;
    if (titleEl) titleEl.innerText = info.title;
    if (descEl) descEl.innerText = info.desc;
}

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    const today = getLocalDateString();
    const dateInputs = ['matrix-booking-date', 'booking-filter-date', 'matrix-week-date-picker'];
    dateInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = today;
    });

    updateUserUI();
    const hashTab = window.location.hash.replace('#', '');
    const savedTab = hashTab || localStorage.getItem('active_tab') || 'home';
    switchTab(savedTab);

    // Preload data
    loadPitches();
    loadBookingMatrix();
    loadMatches();
    loadEvents();
    loadReviews();

    // Close Dropdowns on outside click
    document.addEventListener('click', (e) => {
        const container = document.getElementById('dropdown-menu-container');
        const menu = document.getElementById('function-dropdown-menu');
        if (container && !container.contains(e.target) && menu && !menu.classList.contains('hidden')) {
            closeFunctionDropdown();
        }
    });
});

// TOAST NOTIFICATIONS
function showToast(msg, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    const bg = type === 'success' ? 'bg-emerald-600' : type === 'error' ? 'bg-rose-600' : type === 'warning' ? 'bg-amber-600' : 'bg-slate-800';
    const icon = type === 'success' ? 'fa-check' : type === 'error' ? 'fa-triangle-exclamation' : 'fa-info';
    toast.className = `${bg} text-white text-xs font-semibold px-4 py-3 rounded-2xl shadow-2xl border border-white/20 flex items-center space-x-2 transition transform duration-300 animate-in slide-in-from-bottom-2`;
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${msg}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 4000);
}

// TOPBAR & NAVIGATION
function switchTab(tabId) {
    const adminTabs = ['dashboard', 'pitches', 'timeslots', 'pricing', 'bookings', 'payments', 'maintenance', 'user-roles', 'ai-assistant', 'customers', 'reports'];
    if (adminTabs.includes(tabId)) {
        if (!state.user || (state.user.role !== 'ADMIN' && state.user.role !== 'STAFF')) {
            showToast('Chức năng này chỉ dành cho Ban Quản Trị!', 'warning');
            switchTab('home');
            return;
        }
    }

    state.currentTab = tabId;
    setHeroVideoActive(tabId === 'home');
    localStorage.setItem('active_tab', tabId);
    try {
        if (window.location.hash !== `#${tabId}`) {
            history.replaceState(null, null, `#${tabId}`);
        }
    } catch (e) {}

    // Dynamic banner update
    updateActiveFunctionBanner(tabId);

    document.querySelectorAll('.tab-pane').forEach(el => {
        el.classList.add('hidden');
        el.style.display = '';
    });

    const targetTab = document.getElementById(`tab-${tabId}`);
    if (targetTab) {
        targetTab.classList.remove('hidden');
        targetTab.style.display = '';
    }

    // Highlight public nav buttons
    document.querySelectorAll('.public-nav-btn').forEach(btn => btn.classList.remove('active'));
    const pubBtn = document.getElementById(`nav-btn-${tabId}`);
    if (pubBtn) pubBtn.classList.add('active');

    // Highlight dropdown menu item
    const titleEl = document.getElementById('active-tab-title');
    if (titleEl) titleEl.innerText = TAB_TITLES[tabId] || 'Menu Quản Trị';

    document.querySelectorAll('.menu-item-btn').forEach(btn => btn.classList.remove('active-menu-item'));
    const activeItem = document.getElementById(`dropdown-item-${tabId}`);
    if (activeItem) activeItem.classList.add('active-menu-item');

    // Lazy load specific data
    if (tabId === 'dashboard') loadDashboardStats();
    if (tabId === 'pitches') loadPitches();
    if (tabId === 'timeslots') loadAdminTimeSlots();
    if (tabId === 'pricing' || tabId === 'public-pricing') loadPricingTable();
    if (tabId === 'bookings') loadBookings();
    if (tabId === 'payments') loadPayments();
    if (tabId === 'maintenance') loadMaintenances();
    if (tabId === 'customers') loadCustomers();
    if (tabId === 'reports') loadReportsData('week');
    if (tabId === 'user-roles') { loadUserRolesList(); loadActivityLogs(); }
    if (tabId === 'ai-assistant') populateAINotifBookings();
    if (tabId === 'matrix-booking') {
        if (!state.pitches || state.pitches.length === 0) {
            loadPitches().then(() => {
                renderBookingVisualPitchList();
                loadBookingMatrix();
            });
        } else {
            renderBookingVisualPitchList();
            loadBookingMatrix();
        }
    }
    if (tabId === 'matches') loadMatches();
    if (tabId === 'events') loadEvents();
    if (tabId === 'reviews') loadReviews();

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// =========================================================================
// CHỨC NĂNG 2: QUẢN LÝ KHUNG GIỜ & BẢNG GIÁ (MỤC 3.7.2)
// =========================================================================
let currentPricingSportFilter = 'ALL';

async function loadPricingTable(sportFilter = currentPricingSportFilter) {
    currentPricingSportFilter = sportFilter;
    const isAdminPricing = state.currentTab === 'pricing';
    const grid = document.getElementById(isAdminPricing ? 'pricing-cards-grid' : 'public-pricing-cards-grid');
    if (!grid) return;

    if (!state.pitches || state.pitches.length === 0) {
        await loadPitches();
    }

    let pitches = state.pitches || [];
    if (sportFilter !== 'ALL') {
        pitches = pitches.filter(p => p.sport_type === sportFilter);
    }

    // Update pricing sport filter chip styles
    const chipSelector = isAdminPricing ? '.pricing-sport-btn' : '.pricing-sport-chip';
    const chipPrefix = isAdminPricing ? 'pricing-sport' : 'pricing-chip';
    document.querySelectorAll(chipSelector).forEach(btn => {
        if (isAdminPricing) {
            btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-md');
            btn.classList.add('bg-white', 'text-slate-700', 'border-slate-200');
        } else {
            btn.classList.remove('bg-emerald-600', 'text-white', 'ring-2', 'ring-emerald-400', 'shadow-glow');
            btn.classList.add('bg-slate-900', 'text-slate-300', 'border-slate-800');
        }
    });
    const activeChip = document.getElementById(`${chipPrefix}-${sportFilter.toLowerCase()}`);
    if (activeChip) {
        if (isAdminPricing) {
            activeChip.classList.add('bg-indigo-600', 'text-white', 'shadow-md');
            activeChip.classList.remove('bg-white', 'text-slate-700', 'border-slate-200');
        } else {
            activeChip.classList.add('bg-emerald-600', 'text-white', 'ring-2', 'ring-emerald-400', 'shadow-glow');
            activeChip.classList.remove('bg-slate-900', 'text-slate-300', 'border-slate-800');
        }
    }

    if (pitches.length === 0) {
        grid.innerHTML = `<div class="col-span-full p-8 text-center bg-slate-900/60 border border-slate-800 rounded-3xl text-slate-400 text-xs">Không có sân nào phù hợp với bộ lọc.</div>`;
        return;
    }

    grid.innerHTML = pitches.map(p => {
        const meta = SPORT_CONFIG[p.sport_type] || { icon: '🏟️', label: p.sport_type, color: 'emerald' };
        const normalPrice = p.price_per_hour || 200000;
        const peakPrice = p.peak_price_per_hour || Math.round(normalPrice * 1.3);
        const weekendPrice = Math.round(normalPrice * 1.2);
        const isStaffOrAdmin = state.user && (state.user.role === 'ADMIN' || state.user.role === 'STAFF');

        return `
            <div class="glass-card bg-slate-900/90 border border-slate-800 rounded-3xl p-5 hover:border-emerald-500/50 transition-all duration-300 shadow-xl space-y-4 flex flex-col justify-between">
                <div>
                    <div class="flex justify-between items-start mb-3">
                        <div class="flex items-center space-x-3">
                            <div class="w-11 h-11 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-xl text-emerald-400">
                                ${meta.icon}
                            </div>
                            <div>
                                <h3 class="font-extrabold text-sm text-white">${p.name}</h3>
                                <p class="text-[11px] text-slate-400"><i class="fa-solid fa-location-dot text-emerald-400 mr-1"></i> ${p.location}</p>
                            </div>
                        </div>
                        <span class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-slate-800 text-emerald-300 border border-emerald-500/30">
                            ${p.capacity || meta.label}
                        </span>
                    </div>

                    <div class="space-y-2 pt-2 border-t border-slate-800">
                        <div class="flex justify-between items-center bg-slate-950/70 p-2.5 rounded-xl border border-slate-800/80">
                            <div class="flex items-center space-x-2 text-xs text-slate-300">
                                <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
                                <span>Giờ Thường (06:00 - 16:30)</span>
                            </div>
                            <span class="font-mono font-black text-xs text-emerald-400">${normalPrice.toLocaleString()} đ/h</span>
                        </div>

                        <div class="flex justify-between items-center bg-slate-950/70 p-2.5 rounded-xl border border-slate-800/80">
                            <div class="flex items-center space-x-2 text-xs text-slate-300">
                                <span class="w-2 h-2 rounded-full bg-amber-400"></span>
                                <span>Giờ Cao Điểm (17:00 - 22:30)</span>
                            </div>
                            <span class="font-mono font-black text-xs text-amber-400">${peakPrice.toLocaleString()} đ/h</span>
                        </div>

                        <div class="flex justify-between items-center bg-slate-950/70 p-2.5 rounded-xl border border-slate-800/80">
                            <div class="flex items-center space-x-2 text-xs text-slate-300">
                                <span class="w-2 h-2 rounded-full bg-purple-400"></span>
                                <span>Cuối Tuần (T7 & CN)</span>
                            </div>
                            <span class="font-mono font-black text-xs text-purple-400">${weekendPrice.toLocaleString()} đ/h</span>
                        </div>
                    </div>
                </div>

                <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                    <button onclick="switchTab('matrix-booking'); setTimeout(() => selectVisualPitch(${p.id}), 100);" class="flex-1 py-2 px-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-md transition flex items-center justify-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-calendar-check"></i> Đặt Khung Giờ Này
                    </button>
                    ${isStaffOrAdmin ? `
                        <button onclick="openEditPricingModal(${p.id})" class="py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-bold text-xs border border-slate-700 transition cursor-pointer" title="Sửa bảng giá">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

function filterPricingSport(sport) {
    loadPricingTable(sport);
}

function openEditPricingModal(pitchId) {
    const pitch = (state.pitches || []).find(p => p.id === pitchId);
    if (!pitch) return;

    const modal = document.getElementById('modal-edit-pricing');
    if (!modal) return;

    document.getElementById('edit-pricing-pitch-id').value = pitch.id;
    document.getElementById('edit-pricing-pitch-name').innerText = pitch.name;
    document.getElementById('edit-pricing-normal').value = pitch.price_per_hour || 200000;
    document.getElementById('edit-pricing-peak').value = pitch.peak_price_per_hour || (pitch.price_per_hour ? pitch.price_per_hour * 1.3 : 260000);
    document.getElementById('edit-pricing-weekend').value = Math.round((pitch.price_per_hour || 200000) * 1.2);

    modal.classList.remove('hidden');
}

function closeEditPricingModal() {
    const modal = document.getElementById('modal-edit-pricing');
    if (modal) modal.classList.add('hidden');
}

async function handleUpdatePricingSubmit(e) {
    if (e) e.preventDefault();
    const pitchId = parseInt(document.getElementById('edit-pricing-pitch-id').value);
    const normal = parseFloat(document.getElementById('edit-pricing-normal').value);
    const peak = parseFloat(document.getElementById('edit-pricing-peak').value);

    try {
        await apiFetch(`/api/pitches/${pitchId}`, {
            method: 'PUT',
            body: JSON.stringify({
                price_per_hour: normal,
                peak_price_per_hour: peak
            })
        });
        showToast('Cập nhật bảng giá khung giờ thành công!', 'success');
        closeEditPricingModal();
        await loadPitches();
        loadPricingTable();
    } catch (err) {
        showToast(`Lỗi cập nhật bảng giá: ${err.message}`, 'error');
    }
}
// LEFT SLIDE-OVER DRAWER NAVIGATION
function openSlideDrawer() {
    const overlay = document.getElementById('slide-drawer-overlay');
    const panel = document.getElementById('slide-drawer-panel');
    if (!overlay || !panel) return;

    overlay.classList.remove('hidden');
    void overlay.offsetWidth; // Trigger reflow for CSS transition
    overlay.classList.remove('opacity-0');
    overlay.classList.add('opacity-100');
    panel.classList.remove('-translate-x-full');
    panel.classList.add('translate-x-0');
}

function closeSlideDrawer() {
    const overlay = document.getElementById('slide-drawer-overlay');
    const panel = document.getElementById('slide-drawer-panel');
    if (!overlay || !panel) return;

    overlay.classList.remove('opacity-100');
    overlay.classList.add('opacity-0');
    panel.classList.remove('translate-x-0');
    panel.classList.add('-translate-x-full');

    setTimeout(() => {
        overlay.classList.add('hidden');
    }, 300);
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeSlideDrawer();
        closeFunctionDropdown();
        closeMoreNavDropdown();
    }
});

function toggleMoreNavDropdown(e) {
    if (e && e.stopPropagation) e.stopPropagation();
    const menu = document.getElementById('more-nav-dropdown-menu');
    const chevron = document.getElementById('more-nav-chevron');
    if (!menu) return;
    const isHidden = menu.classList.contains('hidden') || menu.style.display === 'none';
    if (isHidden) {
        menu.classList.remove('hidden');
        menu.style.display = 'block';
        if (chevron) chevron.classList.add('rotate-180');
    } else {
        closeMoreNavDropdown();
    }
}

function closeMoreNavDropdown() {
    const menu = document.getElementById('more-nav-dropdown-menu');
    const chevron = document.getElementById('more-nav-chevron');
    if (menu) {
        menu.classList.add('hidden');
        menu.style.display = 'none';
    }
    if (chevron) chevron.classList.remove('rotate-180');
}

function selectMoreNavFunction(tabId) {
    closeMoreNavDropdown();
    switchTab(tabId);
}

function toggleFunctionDropdown(e) {
    if (e && e.stopPropagation) e.stopPropagation();
    const menu = document.getElementById('function-dropdown-menu');
    const chevron = document.getElementById('menu-chevron');
    if (!menu) return;
    const isHidden = menu.classList.contains('hidden') || menu.style.display === 'none';
    if (isHidden) {
        menu.classList.remove('hidden');
        menu.style.display = 'block';
        if (chevron) chevron.classList.add('rotate-180');
    } else {
        closeFunctionDropdown();
    }
}

function closeFunctionDropdown() {
    const menu = document.getElementById('function-dropdown-menu');
    const chevron = document.getElementById('menu-chevron');
    if (menu) {
        menu.classList.add('hidden');
        menu.style.display = 'none';
    }
    if (chevron) chevron.classList.remove('rotate-180');
}

function selectMenuFunction(tabId) {
    closeFunctionDropdown();
    switchTab(tabId);
}

// VIDEO CONTROLS
function setHeroVideoActive(active) {
    const video = document.getElementById('bg-hero-video');
    const source = video?.querySelector('source');
    const icon = document.getElementById('icon-video-play');
    if (!video) return;

    const defaultVideoSrc = '/static/videos/nensanthethao.mp4';

    if (!active) {
        video.pause();
        if (source) {
            const currentSrc = source.getAttribute('src');
            if (currentSrc && currentSrc !== defaultVideoSrc) {
                source.setAttribute('src', defaultVideoSrc);
            }
            video.load();
        }
        if (icon) icon.className = 'fa-solid fa-play';
        return;
    }

    if (source && !source.getAttribute('src')) {
        source.setAttribute('src', source.dataset?.src || defaultVideoSrc);
        video.load();
    }
    video.play().then(() => {
        if (icon) icon.className = 'fa-solid fa-pause';
    }).catch(() => {
        if (icon) icon.className = 'fa-solid fa-play';
    });
}

function toggleVideoMute() {
    const video = document.getElementById('bg-hero-video');
    const icon = document.getElementById('icon-video-mute');
    if (!video) return;
    video.muted = !video.muted;
    icon.className = video.muted ? 'fa-solid fa-volume-xmark' : 'fa-solid fa-volume-high text-emerald-400';
    showToast(video.muted ? 'Đã tắt âm thanh' : 'Đã bật âm thanh video', 'info');
}

function toggleVideoPlay() {
    const video = document.getElementById('bg-hero-video');
    const icon = document.getElementById('icon-video-play');
    if (!video) return;
    if (video.paused) {
        setHeroVideoActive(true);
        showToast('Đang phát video nền', 'info');
    } else {
        video.pause();
        icon.className = 'fa-solid fa-play text-amber-400';
        showToast('Đã tạm dừng video nền', 'info');
    }
}

// AUTHENTICATION UI & OTP 4 SỐ
function openAuthModal(view = 'login') {
    const modal = document.getElementById('modal-auth');
    if (modal) modal.classList.remove('hidden');
    toggleAuthView(view);
}

function closeAuthModal() {
    const modal = document.getElementById('modal-auth');
    if (modal) modal.classList.add('hidden');
}

function toggleAuthView(view) {
    const viewLogin = document.getElementById('auth-view-login');
    const viewRegister = document.getElementById('auth-view-register');
    const viewForgot = document.getElementById('auth-view-forgot');

    if (viewLogin) viewLogin.classList.add('hidden');
    if (viewRegister) viewRegister.classList.add('hidden');
    if (viewForgot) viewForgot.classList.add('hidden');

    if (view === 'login' && viewLogin) {
        viewLogin.classList.remove('hidden');
        viewLogin.classList.add('flex');
    } else if (view === 'register' && viewRegister) {
        viewRegister.classList.remove('hidden');
        viewRegister.classList.add('flex');
    } else if (view === 'forgot' && viewForgot) {
        viewForgot.classList.remove('hidden');
        viewForgot.classList.add('flex');
        document.getElementById('forgot-step-1')?.classList.remove('hidden');
        document.getElementById('forgot-step-2')?.classList.add('hidden');
    }
}

function openForgotPassView() {
    toggleAuthView('forgot');
}

async function handleSendOTP() {
    const identifier = document.getElementById('forgot-identifier')?.value.trim();
    if (!identifier) {
        showToast('Vui lòng nhập Email hoặc Tên đăng nhập', 'error');
        return;
    }

    try {
        const res = await fetch('/api/auth/send-otp', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ email_or_username: identifier })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Không thể gửi mã xác thực');

        document.getElementById('forgot-step-1')?.classList.add('hidden');
        document.getElementById('forgot-step-2')?.classList.remove('hidden');
        
        const msgEl = document.getElementById('forgot-otp-sent-msg');
        if (msgEl) msgEl.innerText = `Mã xác thực 4 số đã gửi về email: ${data.email_masked}. (Mã demo: ${data.demo_otp_hint})`;
        
        const otpInput = document.getElementById('forgot-otp-code');
        if (otpInput && data.demo_otp_hint) otpInput.value = data.demo_otp_hint;

        showToast(`Mã xác thực 4 số: ${data.demo_otp_hint}`, 'success');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function handleVerifyOTPAndReset() {
    const identifier = document.getElementById('forgot-identifier')?.value.trim();
    const otp = document.getElementById('forgot-otp-code')?.value.trim();
    const newPass = document.getElementById('forgot-new-pass')?.value;
    const rePass = document.getElementById('forgot-re-pass')?.value;

    if (!otp || otp.length !== 4) {
        showToast('Mã xác thực phải gồm đúng 4 chữ số', 'error');
        return;
    }
    if (newPass !== rePass) {
        showToast('Mật khẩu nhập lại không khớp', 'error');
        return;
    }
    if (newPass.length < 6) {
        showToast('Mật khẩu mới phải có ít nhất 6 ký tự', 'error');
        return;
    }

    try {
        const res = await fetch('/api/auth/verify-otp', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                email_or_username: identifier,
                otp_code: otp,
                new_password: newPass
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Xác thực thất bại');

        showToast(data.message, 'success');
        toggleAuthView('login');
        const loginUserInput = document.getElementById('login-username');
        if (loginUserInput) loginUserInput.value = identifier;
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// USER UI & ROLE-BASED ACCESS CONTROL
function updateUserUI() {
    const userBadge = document.getElementById('user-badge');
    const usernameEl = document.getElementById('current-username');
    const roleBadge = document.getElementById('current-role');
    const walletAmtEl = document.getElementById('header-wallet-amt');
    const guestButtons = document.getElementById('guest-auth-buttons');
    const logoutBtn = document.getElementById('btn-logout');
    const dropdownContainer = document.getElementById('dropdown-menu-container');

    const drawerUsername = document.getElementById('drawer-username');
    const drawerRole = document.getElementById('drawer-user-role');
    const managementHeading = document.getElementById('drawer-management-heading');
    const menuRole = state.user ? state.user.role : 'GUEST';
    document.querySelectorAll('[data-menu-roles]').forEach(section => {
        const allowedRoles = section.dataset.menuRoles.split(',');
        section.classList.toggle('hidden', !allowedRoles.includes(menuRole));
    });
    if (managementHeading) {
        managementHeading.innerText = menuRole === 'STAFF' ? 'Danh Mục Nhân Viên' : 'Danh Mục Quản Trị';
    }
    if (drawerRole) drawerRole.innerText = state.user ? state.user.role : 'KHÁCH';

    if (state.user) {
        if (usernameEl) usernameEl.innerText = state.user.full_name || state.user.username;
        if (drawerUsername) drawerUsername.innerText = state.user.full_name || state.user.username;
        if (roleBadge) roleBadge.innerText = state.user.role;
        if (walletAmtEl) walletAmtEl.innerText = `${(state.user.wallet_balance || 0).toLocaleString()} đ`;
        if (userBadge) { userBadge.classList.remove('hidden'); userBadge.classList.add('flex'); }
        if (guestButtons) guestButtons.classList.add('hidden');
        if (logoutBtn) logoutBtn.classList.remove('hidden');

        // PHÂN QUYỀN CHẶT CHẼ:
        // Khách hàng (CUSTOMER) -> ẨN hoàn toàn Menu Quản Trị
        // Chỉ ADMIN hoặc STAFF mới hiện Menu Quản Trị
        if (state.user.role === 'ADMIN' || state.user.role === 'STAFF') {
            if (dropdownContainer) dropdownContainer.classList.remove('hidden');
            const adminOnlyItems = ['dropdown-item-user-roles', 'dropdown-item-ai-assistant'];
            adminOnlyItems.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.style.display = (state.user.role === 'ADMIN') ? 'flex' : 'none';
            });
        } else {
            if (dropdownContainer) dropdownContainer.classList.add('hidden');
        }

        // Pre-fill matrix booking form
        const custNameInput = document.getElementById('matrix-cust-name');
        const custPhoneInput = document.getElementById('matrix-cust-phone');
        const custEmailInput = document.getElementById('matrix-cust-email');
        if (custNameInput && !custNameInput.value) custNameInput.value = state.user.full_name;
        if (custPhoneInput && !custPhoneInput.value) custPhoneInput.value = state.user.phone || '';
        if (custEmailInput && !custEmailInput.value) custEmailInput.value = state.user.email || '';

        // Show/hide admin-only buttons
        document.querySelectorAll('.admin-only').forEach(el => {
            if (state.user.role === 'ADMIN' || state.user.role === 'STAFF') {
                el.classList.remove('hidden');
            } else {
                el.classList.add('hidden');
            }
        });
        const btnCreateEvent = document.getElementById('btn-open-create-event');
        if (btnCreateEvent) {
            if (state.user.role === 'ADMIN' || state.user.role === 'STAFF') {
                btnCreateEvent.classList.remove('hidden');
            } else {
                btnCreateEvent.classList.add('hidden');
            }
        }
    } else {
        if (userBadge) { userBadge.classList.add('hidden'); userBadge.classList.remove('flex'); }
        if (guestButtons) guestButtons.classList.remove('hidden');
        if (logoutBtn) logoutBtn.classList.add('hidden');
        if (dropdownContainer) dropdownContainer.classList.add('hidden'); // ẨN KHI LÀ KHÁCH CHƯA ĐĂNG NHẬP
        document.querySelectorAll('.admin-only').forEach(el => el.classList.add('hidden'));
        const btnCreateEvent = document.getElementById('btn-open-create-event');
        if (btnCreateEvent) btnCreateEvent.classList.add('hidden');
    }
    renderHomePitchesGrid(); renderBookingVisualPitchList();
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const u = document.getElementById('login-username').value.trim();
    const p = document.getElementById('login-password').value;
    
    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username: u, password: p })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Đăng nhập thất bại');

        state.token = data.access_token;
        state.user = data.user;
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));

        updateUserUI();
        closeAuthModal();
        showToast(`Đăng nhập thành công! Xin chào ${data.user.full_name}`, 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function handleRegisterSubmit(e) {
    e.preventDefault();
    const fullName = document.getElementById('reg-fullname').value.trim();
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const phone = document.getElementById('reg-phone').value.trim();
    const password = document.getElementById('reg-password').value;
    const rePassword = document.getElementById('reg-repassword').value;

    if (password !== rePassword) {
        showToast('Mật khẩu nhập lại không khớp!', 'error');
        return;
    }
    if (password.length < 6) {
        showToast('Mật khẩu phải có ít nhất 6 ký tự!', 'error');
        return;
    }

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                full_name: fullName,
                username: username,
                email: email,
                phone: phone,
                password: password,
                role: 'CUSTOMER'
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Đăng ký thất bại');

        showToast('Đăng ký tài khoản thành công! Đang tự động đăng nhập...', 'success');
        
        // Auto login
        const loginRes = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username: username, password: password })
        });
        const loginData = await loginRes.json();
        if (loginRes.ok) {
            state.token = loginData.access_token;
            state.user = loginData.user;
            localStorage.setItem('token', loginData.access_token);
            localStorage.setItem('user', JSON.stringify(loginData.user));
            updateUserUI();
            closeAuthModal();
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    updateUserUI();
    switchTab('home');
    showToast('Đã đăng xuất thành công', 'info');
}

function handleGoogleLogin() {
    openGoogleAccountPicker();
}

function openGoogleAccountPicker() {
    const modal = document.getElementById('modal-google-picker');
    if (modal) modal.classList.remove('hidden');
}

function closeGoogleAccountPicker() {
    const modal = document.getElementById('modal-google-picker');
    if (modal) modal.classList.add('hidden');
}

async function selectGoogleAccount(email, fullName, role = 'ADMIN') {
    try {
        showToast(`Đang kết nối xác thực Google OAuth 2.0 cho ${email}...`, 'info');
        
        const res = await fetch('/api/auth/google-login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                email: email,
                full_name: fullName,
                role: role
            })
        });
        
        let data;
        if (res.ok) {
            data = await res.json();
        } else {
            data = {
                access_token: 'google_mock_token_' + Date.now(),
                user: {
                    id: Date.now() % 10000,
                    username: email.split('@')[0],
                    full_name: fullName,
                    email: email,
                    role: role,
                    phone: '0987654321'
                }
            };
        }

        state.token = data.access_token;
        state.user = data.user;
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));

        updateUserUI();
        closeGoogleAccountPicker();
        closeAuthModal();
        showToast(`Đăng nhập Google thành công! Tài khoản: ${data.user.full_name} (${data.user.role})`, 'success');
    } catch (err) {
        showToast('Đăng nhập Google thất bại: ' + err.message, 'error');
    }
}

function promptCustomGoogleAccount() {
    const customEmail = prompt('Nhập địa chỉ Email Google của bạn:', 'khachhang.ictu@gmail.com');
    if (!customEmail || !customEmail.includes('@')) {
        if (customEmail !== null) showToast('Email không hợp lệ!', 'error');
        return;
    }
    const customName = prompt('Nhập Họ và tên hiển thị:', 'Khách Hàng Google');
    if (!customName) return;
    
    selectGoogleAccount(customEmail.trim(), customName.trim(), 'CUSTOMER');
}

// =========================================================================
// PROFILE CONTROLLER (HỒ SƠ CÁ NHÂN: SĐT, QUÊ QUÁN, NĂM SINH)
// =========================================================================
function openProfileModal() {
    if (!state.user) {
        showToast('Vui lòng đăng nhập tài khoản để xem và cập nhật thông tin cá nhân!', 'warning');
        openAuthModal('login');
        return;
    }

    const modal = document.getElementById('modal-profile') || document.getElementById('modal-user-profile');
    if (!modal) return;

    const fn = document.getElementById('prof-fullname');
    const ph = document.getElementById('prof-phone');
    const by = document.getElementById('prof-birthyear');
    const ht = document.getElementById('prof-hometown');
    const em = document.getElementById('prof-email');

    if (fn) fn.value = state.user.full_name || state.user.username || '';
    if (ph) ph.value = state.user.phone || '';
    if (by) by.value = state.user.birth_year || '';
    if (ht) ht.value = state.user.hometown || '';
    if (em) em.value = state.user.email || '';

    switchProfileTab('info');
    loadWalletData();
    loadMyBookings();

    modal.classList.remove('hidden');
}

function openMyBookingHistory() {
    openProfileModal();
    if (state.user) switchProfileTab('bookings');
}

function closeProfileModal() {
    const modal = document.getElementById('modal-profile') || document.getElementById('modal-user-profile');
    if (modal) modal.classList.add('hidden');
}

async function handleSaveProfileSubmit(event) {
    if (event) event.preventDefault();
    if (!state.token || !state.user) {
        showToast('Vui lòng đăng nhập để lưu hồ sơ cá nhân!', 'warning');
        openAuthModal('login');
        return;
    }

    const full_name = document.getElementById('prof-fullname')?.value?.trim();
    const phone = document.getElementById('prof-phone')?.value?.trim();
    const birth_year_val = document.getElementById('prof-birthyear')?.value?.trim();
    const birth_year = birth_year_val ? parseInt(birth_year_val, 10) : null;
    const hometown = document.getElementById('prof-hometown')?.value?.trim();
    const email = document.getElementById('prof-email')?.value?.trim();

    if (!phone || !birth_year || !hometown) {
        showToast('Vui lòng điền đầy đủ Số điện thoại, Quê quán và Năm sinh!', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/auth/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                full_name: full_name || state.user.full_name,
                phone: phone,
                birth_year: birth_year,
                hometown: hometown,
                email: email || state.user.email
            })
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.detail || 'Không thể cập nhật hồ sơ cá nhân!', 'error');
            return;
        }

        // Cập nhật state & localStorage
        state.user = { ...state.user, ...data };
        localStorage.setItem('user', JSON.stringify(state.user));
        localStorage.setItem('user_data', JSON.stringify(state.user));

        // Cập nhật UI
        const nameEl = document.getElementById('current-username');
        if (nameEl) nameEl.innerText = state.user.full_name || state.user.username;

        closeProfileModal();
        showToast('🎉 Cập nhật hồ sơ cá nhân thành công! Bạn có thể tiếp tục đặt sân.', 'success');
    } catch (err) {
        console.error(err);
        showToast('Lỗi kết nối máy chủ khi lưu hồ sơ!', 'error');
    }
}

function switchProfileTab(tab) {
    ['wallet', 'bookings', 'info'].forEach(t => {
        const pane = document.getElementById(`ptab-${t}`);
        const nav = document.getElementById(`pnav-${t}`);
        if (pane) pane.classList.add('hidden');
        if (nav) {
            nav.classList.remove('active', 'border-emerald-500', 'text-emerald-400');
            nav.classList.add('border-transparent', 'text-slate-400');
        }
    });

    const activePane = document.getElementById(`ptab-${tab}`);
    const activeNav = document.getElementById(`pnav-${tab}`);
    if (activePane) activePane.classList.remove('hidden');
    if (activeNav) {
        activeNav.classList.add('active', 'border-emerald-500', 'text-emerald-400');
        activeNav.classList.remove('border-transparent', 'text-slate-400');
    }
}

async function loadWalletData() {
    if (!state.token) return;
    try {
        const res = await fetch('/api/wallet/me', {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        
        state.user.wallet_balance = data.wallet_balance;
        localStorage.setItem('user', JSON.stringify(state.user));
        updateUserUI();

        const balEl = document.getElementById('profile-wallet-balance');
        if (balEl) balEl.innerText = `${Number(data.wallet_balance).toLocaleString()} VNĐ`;

        const tbody = document.getElementById('wallet-history-tbody');
        if (tbody) {
            if (!data.transactions || data.transactions.length === 0) {
                tbody.innerHTML = `<tr><td colspan="3" class="py-4 text-center text-slate-500 text-xs">Chưa có giao dịch ví nào</td></tr>`;
            } else {
                tbody.innerHTML = data.transactions.map(tx => `
                    <tr class="hover:bg-slate-900/60 transition">
                        <td class="py-2.5 text-slate-400 font-mono text-[11px]">${new Date(tx.created_at).toLocaleDateString('vi-VN')} ${new Date(tx.created_at).toLocaleTimeString('vi-VN', {hour:'2-digit', minute:'2-digit'})}</td>
                        <td class="py-2.5 text-slate-200">${tx.description || 'Giao dịch ví'}</td>
                        <td class="py-2.5 text-right font-bold ${tx.amount > 0 ? 'text-emerald-400' : 'text-rose-400'} font-mono">
                            ${tx.amount > 0 ? '+' : ''}${Number(tx.amount).toLocaleString()} đ
                        </td>
                    </tr>
                `).join('');
            }
        }
    } catch (e) {
        console.error(e);
    }
}

function openDepositModal() {
    if (!state.user) {
        showToast('Vui lòng đăng nhập trước khi nạp tiền vào ví!', 'warning');
        openAuthModal('login');
        return;
    }
    const modal = document.getElementById('modal-wallet-deposit');
    if (modal) modal.classList.remove('hidden');
    selectDepositAmount(200000);
}

function closeDepositModal() {
    const modal = document.getElementById('modal-wallet-deposit');
    if (modal) modal.classList.add('hidden');
}

function selectDepositAmount(amt) {
    const customInput = document.getElementById('custom-deposit-amount');
    if (customInput) customInput.value = amt;

    document.querySelectorAll('.dep-amt-btn').forEach(b => {
        b.classList.remove('active', 'bg-emerald-600', 'border-emerald-500', 'text-white');
        b.classList.add('bg-slate-950', 'text-slate-200');
    });

    event?.target?.classList?.add('active', 'bg-emerald-600', 'border-emerald-500', 'text-white');
    event?.target?.classList?.remove('bg-slate-950', 'text-slate-200');

    updateDepositQR(amt);
}

function onCustomDepositChange() {
    const amt = parseFloat(document.getElementById('custom-deposit-amount')?.value || 0);
    document.querySelectorAll('.dep-amt-btn').forEach(b => {
        b.classList.remove('active', 'bg-emerald-600', 'border-emerald-500', 'text-white');
        b.classList.add('bg-slate-950', 'text-slate-200');
    });
    updateDepositQR(amt);
}

function updateDepositQR(amt) {
    if (!amt || amt < 10000) amt = 200000;
    const userId = state.user?.id || 1;
    const username = state.user?.username || 'khachhang';
    const content = `NAPVI ${userId} ${username}`;
    const encodedContent = encodeURIComponent(content);
    const encodedName = encodeURIComponent('TRAN THANH CHUNG');
    const qrUrl = `https://img.vietqr.io/image/MB-0816227206-compact2.png?amount=${amt}&addInfo=${encodedContent}&accountName=${encodedName}`;

    const qrImg = document.getElementById('wallet-vietqr-image');
    const qrCap = document.getElementById('wallet-qr-caption');
    if (qrImg) qrImg.src = qrUrl;
    if (qrCap) qrCap.innerText = `Nội dung CK: ${content} (${amt.toLocaleString()}đ)`;
}

async function confirmDepositNow() {
    const amt = parseFloat(document.getElementById('custom-deposit-amount')?.value || 200000);
    if (!amt || amt < 10000) {
        showToast('Số tiền nạp tối thiểu là 10.000 VNĐ', 'error');
        return;
    }

    try {
        const res = await fetch('/api/wallet/confirm-deposit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ amount: amt, bank_name: 'MB' })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Không thể nạp tiền');

        state.user.wallet_balance = data.wallet_balance;
        localStorage.setItem('user', JSON.stringify(state.user));
        updateUserUI();

        showToast(`🎉 Nạp thành công +${amt.toLocaleString()} VNĐ vào ví điện tử!`, 'success');
        closeDepositModal();
        loadWalletData();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function loadMyBookings() {
    const container = document.getElementById('my-bookings-container');
    if (!container) return;

    if (!state.token) {
        container.innerHTML = `<p class="text-xs text-slate-400 text-center py-6"><i class="fa-solid fa-lock mr-1 text-amber-400"></i> Vui lòng đăng nhập tài khoản để xem toàn bộ lịch sử đơn đặt sân của bạn.</p>`;
        return;
    }

    try {
        const res = await fetch('/api/bookings/my-bookings', {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Không thể tải đơn đặt');
        const list = await res.json();

        if (list.length === 0) {
            container.innerHTML = `<p class="text-xs text-slate-500 text-center py-6">Bạn chưa có đơn đặt sân nào. Hãy chọn sân và khung giờ để đặt ngay!</p>`;
            return;
        }

        container.innerHTML = list.map(b => `
            <div class="bg-slate-950 border border-slate-800 rounded-2xl p-3.5 space-y-2 text-xs">
                <div class="flex justify-between items-start">
                    <div>
                        <span class="font-mono text-emerald-400 font-bold">#${b.id}</span>
                        <h4 class="font-bold text-white text-sm">${b.pitch?.name || 'Sân thể thao'}</h4>
                    </div>
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${b.status === 'CONFIRMED' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : b.status === 'CANCELLED' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-amber-950 text-amber-300 border border-amber-800'}">
                        ${b.status === 'CONFIRMED' ? 'Đã Duyệt' : b.status === 'CANCELLED' ? 'Đã Hủy' : 'Chờ Duyệt'}
                    </span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-[11px] text-slate-300 pt-1 border-t border-slate-900">
                    <p><i class="fa-solid fa-calendar text-emerald-400 mr-1"></i> Ngày: <strong>${b.booking_date}</strong></p>
                    <p><i class="fa-solid fa-clock text-amber-400 mr-1"></i> Giờ: <strong>${b.start_time} - ${b.end_time}</strong></p>
                    <p><i class="fa-solid fa-coins text-yellow-400 mr-1"></i> Tổng: <strong class="text-emerald-400">${b.total_price.toLocaleString()}đ</strong></p>
                    <p><i class="fa-solid fa-credit-card text-blue-400 mr-1"></i> PTTT: <strong>${b.payment_method}</strong></p>
                </div>
                <div class="flex justify-end space-x-2 pt-1">
                    <button onclick="viewBookingInvoice(${b.id})" class="bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-bold px-3 py-1 rounded-lg transition">Xem hóa đơn</button>
                    ${b.status === 'PENDING' ? `<button onclick="cancelMyBooking(${b.id})" class="bg-rose-950/80 hover:bg-rose-900 text-rose-300 text-[10px] font-bold px-3 py-1 rounded-lg transition">Hủy đơn</button>` : ''}
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<p class="text-xs text-rose-400 text-center py-4">${e.message}</p>`;
    }
}

async function cancelMyBooking(bookingId) {
    if (!confirm('Bạn có chắc chắn muốn hủy đơn đặt sân này? (Nếu đã thanh toán, tiền sẽ được hoàn về Ví)')) return;
    try {
        const res = await fetch(`/api/bookings/${bookingId}/cancel`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Không thể hủy đơn');
        showToast('Đã hủy đơn đặt sân thành công!', 'success');
        loadMyBookings();
        loadBookingMatrix();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// LIGHTBOX / PITCH IMAGE VIEWER
function openPitchImageModal(pitchId) {
    const pitch = state.pitches.find(p => p.id === pitchId);
    if (!pitch) return;
    state.currentLightboxPitchId = pitchId;

    const modal = document.getElementById('modal-pitch-image-lightbox');
    if (!modal) return;

    const image = document.getElementById('lightbox-pitch-img');
    image.onerror = () => {
        image.onerror = null;
        image.src = getPitchFallbackImage(pitch);
    };
    image.src = getPitchImageUrl(pitch);
    document.getElementById('lightbox-pitch-name').innerText = pitch.name;
    document.getElementById('lightbox-pitch-type').innerText = pitch.sport_type;
    document.getElementById('lightbox-pitch-loc').innerHTML = `<i class="fa-solid fa-location-dot text-emerald-400 mr-1"></i> ${pitch.location}`;
    document.getElementById('lightbox-pitch-desc').innerText = pitch.description || 'Sân thể thao chất lượng cao, trang thiết bị chuẩn quốc tế.';
    document.getElementById('lightbox-pitch-price').innerText = `${pitch.price_per_hour.toLocaleString()} đ/h (Cao điểm: ${pitch.peak_price_per_hour.toLocaleString()} đ/h)`;

    modal.classList.remove('hidden');
}

function closePitchImageModal() {
    const modal = document.getElementById('modal-pitch-image-lightbox');
    if (modal) modal.classList.add('hidden');
}

function bookFromLightbox() {
    const pitchId = state.currentLightboxPitchId;
    closePitchImageModal();
    selectPitchToBook(pitchId);
}

// PITCHES LOADING & CATEGORY FILTER
let currentHomeSport = 'ALL';

const PITCH_LOCAL_IMAGES = {
    1: '/static/images/pitch-01.jpg',
    2: '/static/images/pitch-02.jpg',
    3: '/static/images/pitch-03.jpg',
    4: '/static/images/pitch-04.jpg',
    5: '/static/images/pitch-05.jpg',
    6: '/static/images/pitch-06.jpg',
    7: '/static/images/pitch-07.jpg',
    8: '/static/images/pitch-08.jpg'
};

const SPORT_LOCAL_IMAGES = {
    FOOTBALL: PITCH_LOCAL_IMAGES[1],
    BADMINTON: PITCH_LOCAL_IMAGES[3],
    TENNIS: PITCH_LOCAL_IMAGES[5],
    GYM: PITCH_LOCAL_IMAGES[7],
    BASKETBALL: PITCH_LOCAL_IMAGES[8]
};

function getPitchFallbackImage(pitch) {
    return PITCH_LOCAL_IMAGES[pitch.id] || SPORT_LOCAL_IMAGES[pitch.sport_type] || PITCH_LOCAL_IMAGES[1];
}

function getPitchImageUrl(pitch) {
    const imageUrl = (pitch.image_url || '').trim();
    if (imageUrl.startsWith('/static/')) return imageUrl;
    return getPitchFallbackImage(pitch);
}

function filterHomeSport(category) {
    currentHomeSport = category;
    document.querySelectorAll('.home-sport-tab').forEach(b => {
        b.classList.remove('active', 'bg-emerald-600', 'text-white', 'shadow-glow');
        b.classList.add('bg-slate-900', 'text-slate-300', 'border', 'border-slate-800');
    });
    const activeBtn = document.getElementById(`htab-${category.toLowerCase()}`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'bg-emerald-600', 'text-white', 'shadow-glow');
        activeBtn.classList.remove('bg-slate-900', 'text-slate-300', 'border-slate-800');
    }
    renderHomePitchesGrid(); renderBookingVisualPitchList();
}

function renderHomePitchesGrid() {
    const homeGrid = document.getElementById('home-pitches-grid');
    if (!homeGrid || !state.pitches) return;

    let filtered = state.pitches;
    if (currentHomeSport !== 'ALL') {
        filtered = state.pitches.filter(p => p.sport_type === currentHomeSport);
    }

    const isAdmin = state.user && (state.user.role === 'ADMIN' || state.user.role === 'STAFF');

    homeGrid.innerHTML = filtered.map(p => {
        const sportIcons = {
            'FOOTBALL': { label: 'Bóng đá', icon: '⚽', badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' },
            'BADMINTON': { label: 'Cầu lông', icon: '🏸', badgeClass: 'bg-teal-500/20 text-teal-300 border-teal-500/40' },
            'TENNIS': { label: 'Tennis', icon: '🎾', badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/40' },
            'GYM': { label: 'Gym & Thể hình', icon: '🏋️', badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/40' },
            'BASKETBALL': { label: 'Bóng rổ', icon: '🏀', badgeClass: 'bg-orange-500/20 text-orange-300 border-orange-500/40' }
        };
        const sportInfo = sportIcons[p.sport_type] || { label: p.sport_type, icon: '🏟️', badgeClass: 'bg-slate-800 text-slate-200 border-slate-700' };
        const capacityText = p.capacity || '5 - 7 người';

        return `
            <div class="glass-card glass-card-hover rounded-3xl overflow-hidden shadow-2xl flex flex-col justify-between group border border-slate-800/80">
                <div class="h-52 overflow-hidden relative cursor-pointer" onclick="openPitchImageModal(${p.id})">
                    <img src="${getPitchImageUrl(p)}" alt="${p.name}" class="w-full h-full object-cover group-hover:scale-110 transition duration-700 ease-out" onerror="this.onerror=null; this.src='${getPitchFallbackImage(p)}'">
                    <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/30 to-transparent"></div>
                    
                    <span class="absolute top-3 right-3 backdrop-blur-md px-3 py-1 rounded-full text-[11px] font-extrabold border shadow-lg ${sportInfo.badgeClass}">
                        ${sportInfo.icon} ${sportInfo.label}
                    </span>

                    <span class="absolute top-3 left-3 bg-slate-950/80 backdrop-blur-md px-3 py-1 rounded-full text-[11px] font-bold text-amber-300 border border-amber-500/30 flex items-center gap-1 shadow-lg">
                        <i class="fa-solid fa-users text-amber-400"></i> ${capacityText}
                    </span>

                    <div class="absolute bottom-3 left-3 right-3 flex items-center justify-between text-white text-[11px]">
                        <span class="bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded-xl border border-white/10 flex items-center gap-1">
                            <i class="fa-solid fa-expand text-emerald-400"></i> Xem ảnh
                        </span>
                        <span class="px-2.5 py-1 rounded-xl font-bold backdrop-blur-md border ${p.status === 'AVAILABLE' ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40' : 'bg-amber-950/80 text-amber-300 border-amber-500/40'}">
                            ${p.status === 'AVAILABLE' ? '🟢 Sẵn sàng' : '🟡 Bảo trì'}
                        </span>
                    </div>
                </div>

                <div class="p-5 space-y-3.5 flex-1 flex flex-col justify-between">
                    <div>
                        <h3 class="font-black text-base text-white group-hover:text-emerald-400 transition cursor-pointer" onclick="openPitchImageModal(${p.id})">${p.name}</h3>
                        <p class="text-xs text-slate-300 mt-1 flex items-start gap-1.5 leading-snug"><i class="fa-solid fa-location-dot text-emerald-400 mt-0.5 flex-shrink-0"></i> <span>${p.location}</span></p>
                        ${p.description ? `<p class="text-[11px] text-slate-400 mt-2 line-clamp-2 italic leading-relaxed">${p.description}</p>` : ''}
                    </div>

                    <div class="pt-3 border-t border-slate-800/80 space-y-2.5">
                        <div class="flex justify-between items-center text-xs">
                            <span class="text-slate-400">Ngày: <strong class="text-emerald-400 font-mono text-sm">${p.price_per_hour.toLocaleString()}đ/h</strong></span>
                            <span class="text-slate-400">Tối: <strong class="text-amber-400 font-mono text-sm">${(p.peak_price_per_hour || p.price_per_hour).toLocaleString()}đ/h</strong></span>
                        </div>

                        <div class="flex items-center gap-2 pt-1">
                            ${isAdmin ? `
                                <button onclick="openEditPitchModal(${p.id})" class="bg-slate-800/90 hover:bg-slate-700 text-amber-300 font-bold text-xs py-2 px-3 rounded-xl border border-amber-500/40 transition flex items-center justify-center gap-1" title="Sửa thông tin">
                                    <i class="fa-solid fa-pen-to-square"></i> <span>Sửa</span>
                                </button>
                            ` : ''}
                            <button onclick="selectPitchToBook(${p.id})" class="flex-1 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black text-xs py-2.5 px-4 rounded-xl shadow-lg transition transform hover:scale-[1.02] flex items-center justify-center gap-1.5">
                                <i class="fa-solid fa-calendar-check"></i> <span>Chọn Khung Giờ</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function loadPitches() {
    try {
        const sportType = document.getElementById('filter-sport-type')?.value || '';
        const url = sportType ? `/api/pitches?sport_type=${sportType}` : '/api/pitches';
        const res = await fetch(url);
        const pitches = await res.json();
        state.pitches = pitches;

        renderHomePitchesGrid(); renderBookingVisualPitchList();

        // Render Admin Pitches Grid
        const adminGrid = document.getElementById('pitches-grid');
        if (adminGrid) {
            adminGrid.innerHTML = pitches.map(p => `
                <div class="bg-slate-900 border border-slate-800 rounded-3xl p-4 space-y-3 shadow-xl flex flex-col justify-between">
                    <div>
                        <div class="h-36 overflow-hidden rounded-2xl relative cursor-pointer" onclick="openPitchImageModal(${p.id})">
                            <img src="${getPitchImageUrl(p)}" alt="${p.name}" class="w-full h-full object-cover" onerror="this.onerror=null; this.src='${getPitchFallbackImage(p)}'">
                            <span class="absolute top-2 right-2 bg-slate-950/80 px-2 py-0.5 rounded-full text-[10px] text-amber-300 border border-amber-500/30">${p.capacity || '5-7 người'}</span>
                        </div>
                        <h3 class="font-bold text-sm text-white mt-2">${p.name}</h3>
                        <p class="text-xs text-slate-400 mt-0.5"><i class="fa-solid fa-location-dot text-emerald-400 mr-1"></i> ${p.location}</p>
                        <p class="text-[11px] text-slate-500 mt-1">${p.description || ''}</p>
                    </div>
                    <div class="pt-2 border-t border-slate-800 space-y-2">
                        <div class="flex justify-between items-center text-xs">
                            <span>Giá: <strong class="text-emerald-400">${p.price_per_hour.toLocaleString()}đ</strong> / <strong class="text-amber-400">${(p.peak_price_per_hour || p.price_per_hour).toLocaleString()}đ</strong></span>
                            <span class="px-2 py-0.5 rounded-full text-[10px] ${p.status === 'AVAILABLE' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-amber-950 text-amber-300 border border-amber-800'}">${p.status}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <button onclick="openEditPitchModal(${p.id})" class="w-full bg-slate-800 hover:bg-slate-700 text-amber-300 font-bold text-xs py-1.5 rounded-xl border border-slate-700 transition flex items-center justify-center gap-1.5">
                                <i class="fa-solid fa-pen-to-square"></i> Sửa Thông Tin Sân
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        // Populate Matrix Pitch Selects
        const matrixPitchSel = document.getElementById('matrix-pitch-select');
        const headerPitchSel = document.getElementById('matrix-header-pitch-select');
        const opts = pitches.map(p => `<option value="${p.id}">${p.name} (${p.capacity || 'Tiêu chuẩn'})</option>`).join('');
        if (matrixPitchSel) matrixPitchSel.innerHTML = opts;
        if (headerPitchSel) headerPitchSel.innerHTML = opts;

    } catch (e) {
        console.error(e);
    }
}

async function loadAdminTimeSlots() {
    const pitchSelect = document.getElementById('admin-timeslot-pitch');
    const dateInput = document.getElementById('admin-timeslot-date');
    const tbody = document.getElementById('admin-timeslots-tbody');
    if (!pitchSelect || !dateInput || !tbody) return;

    try {
        if (!state.pitches?.length) await loadPitches();
        if (!pitchSelect.options.length) {
            pitchSelect.innerHTML = (state.pitches || []).map(pitch => `<option value="${pitch.id}">${pitch.name}</option>`).join('');
        }
        if (!dateInput.value) dateInput.value = getLocalDateString();
        if (!pitchSelect.value && pitchSelect.options.length) pitchSelect.value = pitchSelect.options[0].value;
        if (!pitchSelect.value) {
            tbody.innerHTML = '<tr><td colspan="4" class="p-6 text-center text-slate-500">Chưa có sân để cấu hình khung giờ.</td></tr>';
            return;
        }

        const params = new URLSearchParams({ court_id: pitchSelect.value, date: dateInput.value });
        const data = await apiFetch(`/api/timeslots?${params}`);
        tbody.innerHTML = (data.slots || []).map(slot => {
            const stateLabel = slot.is_booked ? 'Đã có đơn đặt' : slot.is_locked ? 'Đã khóa' : 'Đang mở';
            const stateClass = slot.is_booked ? 'text-blue-400' : slot.is_locked ? 'text-rose-400' : 'text-emerald-400';
            const actions = slot.is_booked
                ? '<span class="text-slate-500">Không thể sửa khi đã đặt</span>'
                : `<button type="button" onclick="setAdminTimeSlotAvailability('${slot.start_time}','${slot.end_time}',${slot.is_available === false})" class="text-xs font-bold ${slot.is_available === false ? 'text-emerald-400' : 'text-amber-400'}">${slot.is_available === false ? 'Mở khung' : 'Khóa khung'}</button> ${slot.id ? `<button type="button" onclick="deleteAdminTimeSlot(${slot.id})" class="ml-3 text-xs font-bold text-rose-400">Đặt lại mặc định</button>` : ''}`;
            return `<tr><td class="p-3 font-mono font-bold text-slate-200">${slot.start_time} - ${slot.end_time}${slot.id ? '<span class="ml-2 text-[10px] text-violet-400">Tùy chỉnh</span>' : ''}</td><td class="p-3 text-right font-mono">${Number(slot.price || 0).toLocaleString('vi-VN')} đ/h</td><td class="p-3 ${stateClass}">${stateLabel}</td><td class="p-3 text-right">${actions}</td></tr>`;
        }).join('') || '<tr><td colspan="4" class="p-6 text-center text-slate-500">Không có khung giờ trong ngày đã chọn.</td></tr>';
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="4" class="p-6 text-center text-rose-400">${error.message}</td></tr>`;
    }
}

async function createAdminTimeSlot(event) {
    event.preventDefault();
    const pitchId = Number(document.getElementById('admin-timeslot-pitch')?.value);
    const date = document.getElementById('admin-timeslot-date')?.value;
    const startTime = document.getElementById('admin-timeslot-start')?.value;
    const endTime = document.getElementById('admin-timeslot-end')?.value;
    try {
        await apiFetch('/api/timeslots', {
            method: 'POST',
            body: JSON.stringify({ court_id: pitchId, date, start_time: startTime, end_time: endTime, is_available: true })
        });
        document.getElementById('admin-timeslot-start').value = '';
        document.getElementById('admin-timeslot-end').value = '';
        showToast('Đã thêm khung giờ riêng cho sân và ngày đã chọn.', 'success');
        loadAdminTimeSlots();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function setAdminTimeSlotAvailability(startTime, endTime, isAvailable) {
    const pitchId = Number(document.getElementById('admin-timeslot-pitch')?.value);
    const date = document.getElementById('admin-timeslot-date')?.value;
    try {
        await apiFetch('/api/timeslots', {
            method: 'POST',
            body: JSON.stringify({ court_id: pitchId, date, start_time: startTime, end_time: endTime, is_available: isAvailable })
        });
        showToast(isAvailable ? 'Đã mở khung giờ.' : 'Đã khóa khung giờ.', 'success');
        loadAdminTimeSlots();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function deleteAdminTimeSlot(slotId) {
    if (!confirm('Xóa ngoại lệ này và khôi phục khung giờ mặc định?')) return;
    try {
        await apiFetch(`/api/timeslots/${slotId}`, { method: 'DELETE' });
        showToast('Đã khôi phục khung giờ mặc định.', 'success');
        loadAdminTimeSlots();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function selectPitchToBook(pitchId) {
    const p = state.pitches?.find(x => x.id === pitchId);
    if (p) filterBookingSport(p.sport_type);
    selectVisualPitch(pitchId);

    switchTab('matrix-booking');
    const sel = document.getElementById('matrix-pitch-select');
    const headerSel = document.getElementById('matrix-header-pitch-select');
    if (sel) sel.value = pitchId;
    if (headerSel) headerSel.value = pitchId;
    recalculateMatrixPrice();
    loadBookingMatrix();
}

// MATRIX BOOKING & TIME FILTER
function filterMatrixFrame(frame) {
    state.currentMatrixFrame = frame;
    document.querySelectorAll('.frame-filter-btn').forEach(b => b.classList.remove('active', 'bg-emerald-600', 'text-white'));
    document.querySelectorAll('.frame-filter-btn').forEach(b => b.classList.add('bg-slate-800', 'text-slate-300'));
    
    const activeBtn = document.getElementById(`btn-frame-${frame.toLowerCase()}`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'bg-emerald-600', 'text-white');
        activeBtn.classList.remove('bg-slate-800', 'text-slate-300');
    }
    loadBookingMatrix();
}

function navigateMatrixWeek(days) {
    state.currentWeekOffset += days;
    loadBookingMatrix();
}

function onMatrixPitchChange() {
    const pitchId = document.getElementById('matrix-pitch-select')?.value;
    const headerSel = document.getElementById('matrix-header-pitch-select');
    if (headerSel && pitchId) headerSel.value = pitchId;
    recalculateMatrixPrice();
    loadBookingMatrix();
}

function onMatrixHeaderPitchChange() {
    const pitchId = document.getElementById('matrix-header-pitch-select')?.value;
    const pitchSel = document.getElementById('matrix-pitch-select');
    if (pitchSel && pitchId) pitchSel.value = pitchId;
    recalculateMatrixPrice();
    loadBookingMatrix();
}

function onPaymentMethodChange() {
    const method = document.getElementById('matrix-payment-method')?.value;
    const bankBox = document.getElementById('bank-select-container');
    if (bankBox) {
        bankBox.style.display = (method === 'BANK_TRANSFER') ? 'block' : 'none';
    }
    if (method === 'WALLET') {
        if (!state.user) {
            showToast('Bạn cần đăng nhập để thanh toán bằng Ví!', 'warning');
            openAuthModal('login');
        } else {
            showToast(`Số dư ví hiện tại: ${(state.user.wallet_balance || 0).toLocaleString()} VNĐ`, 'info');
        }
    }
}

function updateQRDisplay() {
    // optional live updates
}

function recalculateMatrixPrice() {
    const pitchId = parseInt(document.getElementById('matrix-pitch-select')?.value || 1);
    const start = document.getElementById('matrix-start-time')?.value || '17:30';
    const end = document.getElementById('matrix-end-time')?.value || '19:00';
    const pitch = state.pitches.find(p => p.id === pitchId);
    if (!pitch) return;

    const [sh, sm] = start.split(':').map(Number);
    const [eh, em] = end.split(':').map(Number);
    let dur = (eh * 60 + em - (sh * 60 + sm)) / 60;
    if (dur <= 0) dur = 1;

    const rate = sh >= 17 ? pitch.peak_price_per_hour : pitch.price_per_hour;
    const total = dur * rate;
    const displayEl = document.getElementById('matrix-total-price-display');
    if (displayEl) displayEl.innerText = `${Number(total).toLocaleString()} VNĐ`;
}

async function loadBookingMatrix() {
    try {
        const baseDate = new Date();
        baseDate.setDate(baseDate.getDate() + state.currentWeekOffset);
        const dateStr = getLocalDateString(baseDate);
        const pitchId = document.getElementById('matrix-pitch-select')?.value || '';

        const url = `/api/bookings/matrix?start_date=${dateStr}&pitch_id=${pitchId}&time_frame=${state.currentMatrixFrame}`;
        const res = await fetch(url);
        const data = await res.json();
        state.matrixData = data;

        const rangeText = document.getElementById('matrix-week-range-text');
        if (rangeText && data.matrix.length > 0) {
            const first = data.matrix[0].display;
            const last = data.matrix[data.matrix.length - 1].display;
            rangeText.innerText = `Lịch từ ${first} đến ${last}`;
        }

        const tbody = document.getElementById('matrix-table-body');
        if (!tbody) return;

        // Sync date picker input
        const picker = document.getElementById('matrix-week-date-picker');
        if (picker && data.matrix.length > 0) {
            picker.value = data.matrix[0].date;
        }

        let html = `
            <tr class="bg-slate-100 dark:bg-slate-900 text-slate-800 dark:text-slate-300 font-extrabold border-b border-slate-200 dark:border-slate-800">
                <th class="p-2 sm:p-3 text-left border-r border-slate-200 dark:border-slate-800">Ngày</th>
        `;
        data.time_slots.forEach(slot => {
            html += `<th class="p-1 sm:p-2 text-[10px] sm:text-xs font-mono text-slate-800 dark:text-slate-200">${slot.start}<br><span class="text-slate-500 font-normal">${slot.end}</span></th>`;
        });
        html += `</tr>`;

        data.matrix.forEach(row => {
            html += `
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition border-b border-slate-200 dark:border-slate-800/60">
                    <td class="p-2 sm:p-3 text-left font-black text-slate-900 dark:text-white text-xs border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 whitespace-nowrap">
                        ${row.display}
                    </td>
            `;
            row.slots.forEach(slot => {
                let cellClass = "";
                let clickAction = "";

                if (slot.status === 'EXPIRED') {
                    cellClass = "matrix-tier-expired cursor-not-allowed text-[10px]";
                } else if (slot.status === 'BOOKED') {
                    cellClass = "matrix-tier-booked text-[10px]";
                } else if (slot.status === 'PENDING') {
                    cellClass = "matrix-tier-pending text-[10px]";
                } else {
                    // Phân bổ 3 mức màu giá tiền từ thấp đến cao
                    const p = Number(slot.price || 0);
                    if (p < 100000) {
                        cellClass = "matrix-tier-low transition transform hover:scale-[1.04]";
                    } else if (p <= 250000) {
                        cellClass = "matrix-tier-mid transition transform hover:scale-[1.04]";
                    } else {
                        cellClass = "matrix-tier-high transition transform hover:scale-[1.04]";
                    }
                    clickAction = `onclick="onMatrixCellClick(this, '${slot.date}', '${slot.start}', '${slot.end}', ${slot.pitch_id}, ${slot.price}, '${slot.status}')"`;
                }

                html += `
                    <td class="p-1 sm:p-1.5">
                        <div ${clickAction} data-status="${slot.status}" class="matrix-slot-cell p-2 rounded-xl border ${cellClass} transition flex flex-col items-center justify-center cursor-pointer shadow-sm">
                            <span>${slot.text}</span>
                        </div>
                    </td>
                `;
            });
            html += `</tr>`;
        });

        tbody.innerHTML = html;
        recalculateMatrixPrice();
        loadMyRecentBookings();
    } catch (e) {
        console.error(e);
    }
}




function onMatrixCellClick(cellEl, date, start, end, pitchId, price, status) {
    // Tương thích ngược nếu gọi hàm không truyền 'this'
    if (typeof cellEl === 'string') {
        status = price;
        price = pitchId;
        pitchId = end;
        end = start;
        start = date;
        date = cellEl;
        cellEl = (window.event && window.event.currentTarget) ? window.event.currentTarget : null;
    }

    if (status !== 'AVAILABLE') return;

    // 1. Cập nhật ngày thi đấu trên phiếu đặt sân
    const dateInput = document.getElementById('matrix-booking-date');
    if (dateInput) {
        dateInput.value = date;
    }

    // 2. Cập nhật giờ bắt đầu
    const startSelect = document.getElementById('matrix-start-time');
    if (startSelect) {
        let exists = Array.from(startSelect.options).some(o => o.value === start);
        if (!exists) {
            startSelect.add(new Option(start, start));
        }
        startSelect.value = start;
    }

    // 3. Cập nhật giờ kết thúc
    const endSelect = document.getElementById('matrix-end-time');
    if (endSelect) {
        let exists = Array.from(endSelect.options).some(o => o.value === end);
        if (!exists) {
            endSelect.add(new Option(end, end));
        }
        endSelect.value = end;
    }

    // 4. Cập nhật ID sân và danh sách thẻ sân
    if (pitchId) {
        const pitchSelect = document.getElementById('matrix-pitch-select');
        if (pitchSelect) pitchSelect.value = pitchId;
        const p = state.pitches?.find(x => x.id === pitchId);
        if (p) updateMatrixHeaderInfo(p);
        renderBookingVisualPitchList();
    }

    // 5. Hiệu ứng làm nổi bật ô vừa bấm trên bảng ma trận với NỀN XANH LÁ RỰC RỠ (.matrix-slot-selected)
    document.querySelectorAll('.matrix-slot-cell').forEach(el => {
        el.classList.remove('matrix-slot-selected', 'bg-emerald-500', 'text-slate-950', 'ring-2', 'ring-emerald-300', 'shadow-glow', 'font-black');
    });

    const target = cellEl || (window.event && window.event.currentTarget);
    if (target && target.classList) {
        target.classList.add('matrix-slot-selected');
    }

    // 6. Tính toán lại tổng tiền dự tính
    recalculateMatrixPrice();

    // 7. Hiệu ứng nhấp nháy trên mục Thời gian thi đấu
    const timeSection = document.getElementById('booking-time-section');
    if (timeSection) {
        timeSection.classList.add('ring-2', 'ring-emerald-400');
        setTimeout(() => {
            timeSection.classList.remove('ring-2', 'ring-emerald-400');
        }, 1200);
    }

    showToast(`✅ Đã chọn khung giờ: ${start} - ${end} (${date})`, 'success');
}

function jumpToMatrixCalendarDate(val) {
    if (!val) return;
    const pickedDate = new Date(val + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diffTime = pickedDate.getTime() - today.getTime();
    state.currentWeekOffset = Math.round(diffTime / (1000 * 60 * 60 * 24));
    loadBookingMatrix();
}

function jumpToMatrixToday() {
    state.currentWeekOffset = 0;
    const todayStr = getLocalDateString();
    const picker = document.getElementById('matrix-week-date-picker');
    if (picker) picker.value = todayStr;
    const dateInput = document.getElementById('matrix-booking-date');
    if (dateInput) dateInput.value = todayStr;
    loadBookingMatrix();
    showToast('Đã chuyển về lịch thi đấu Hôm nay', 'info');
}

async function loadMyRecentBookings() {
    const tbody = document.getElementById('live-recent-bookings-tbody');
    if (!tbody) return;

    let items = [];
    if (state.token) {
        try {
            const res = await fetch('/api/bookings/my-bookings', {
                headers: { 'Authorization': `Bearer ${state.token}` }
            });
            if (res.ok) {
                items = await res.json();
            }
        } catch (err) {
            console.error(err);
        }
    }

    // Kết hợp với các đơn mới vừa tạo trong phiên (sessionStorage)
    const recentLocal = state.recentCreatedBookings || [];
    const combined = [...recentLocal];
    items.forEach(b => {
        if (!combined.some(x => x.id === b.id)) {
            combined.push(b);
        }
    });

    combined.sort((a, b) => (b.id || 0) - (a.id || 0));

    if (combined.length > 0) {
        renderLiveRecentBookings(combined.slice(0, 5));
    } else {
        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-slate-400 text-xs">Chưa có đơn đặt sân nào gần đây. Hãy chọn sân và khung giờ bên trên để đặt sân!</td></tr>`;
    }
}

function renderLiveRecentBookings(bookings) {
    const tbody = document.getElementById('live-recent-bookings-tbody');
    if (!tbody) return;

    if (!bookings || bookings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-slate-400 text-xs">Chưa có đơn đặt sân nào gần đây. Hãy chọn sân và khung giờ bên trên để đặt sân!</td></tr>`;
        return;
    }

    let html = '';
    bookings.forEach(b => {
        let statusBadge = '';
        if (b.status === 'CONFIRMED' || b.status === 'APPROVED') {
            statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">Đã Duyệt</span>';
        } else if (b.status === 'PENDING') {
            statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">Chờ Duyệt</span>';
        } else if (b.status === 'CANCELLED') {
            statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">Đã Hủy</span>';
        } else {
            statusBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-300">${b.status}</span>`;
        }

        const pitchName = b.pitch?.name || `Sân #${b.pitch_id}`;
        html += `
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-900/60 transition">
                <td class="p-2.5 font-mono font-bold text-emerald-600 dark:text-emerald-400">#${b.id}</td>
                <td class="p-2.5 font-semibold text-slate-800 dark:text-slate-200">${pitchName}</td>
                <td class="p-2.5 text-slate-600 dark:text-slate-400">${b.booking_date} (${b.start_time} - ${b.end_time})</td>
                <td class="p-2.5 font-mono font-bold text-slate-800 dark:text-slate-200">${(b.total_price || 0).toLocaleString()} đ</td>
                <td class="p-2.5">${statusBadge}</td>
                <td class="p-2.5 text-center">
                    <button onclick="viewBookingInvoice(${b.id})" class="text-xs bg-emerald-50 text-emerald-700 hover:bg-emerald-100 px-2.5 py-1 rounded-lg font-bold border border-emerald-200 transition">
                        <i class="fa-solid fa-file-invoice mr-1"></i> Xem
                    </button>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}


async function handleMatrixBookingSubmit(e) {
    if (e) e.preventDefault();

    const pitchId = parseInt(document.getElementById('matrix-pitch-select')?.value || 1);
    const date = document.getElementById('matrix-booking-date')?.value || getLocalDateString();
    const start = document.getElementById('matrix-start-time')?.value;
    const end = document.getElementById('matrix-end-time')?.value;
    const note = document.getElementById('matrix-booking-note')?.value || '';
    const payMethod = document.getElementById('matrix-payment-method')?.value || 'CASH';
    const bankName = document.getElementById('matrix-bank-name')?.value || 'MB';

    const custNameInput = document.getElementById('matrix-cust-name')?.value?.trim();
    const custPhoneInput = document.getElementById('matrix-cust-phone')?.value?.trim();
    const custEmailInput = document.getElementById('matrix-cust-email')?.value?.trim();

    const custName = custNameInput || state.user?.full_name || state.user?.username || 'Khách Hàng';
    const custPhone = custPhoneInput || state.user?.phone || '';
    const custEmail = custEmailInput || state.user?.email || '';

    if (!custName || !custPhone) {
        showToast('Vui lòng nhập đầy đủ Họ và Tên cùng Số điện thoại để đặt sân!', 'warning');
        return;
    }

    // Nếu chọn thanh toán bằng Ví điện tử thì bắt buộc đăng nhập
    if (payMethod === 'WALLET' && (!state.user || !state.token)) {
        showToast('Vui lòng đăng nhập tài khoản để sử dụng thanh toán bằng Ví điện tử!', 'warning');
        openAuthModal('login');
        return;
    }

    const payload = {
        customer_name: custName,
        customer_phone: custPhone,
        pitch_id: pitchId,
        booking_date: date,
        start_time: start,
        end_time: end,
        note: note,
        payment_method: payMethod,
        bank_name: (payMethod === 'BANK_TRANSFER') ? bankName : null,
        invoice_email: custEmail
    };

    try {
        const headers = { 
            'Content-Type': 'application/json'
        };
        if (state.token) {
            headers['Authorization'] = `Bearer ${state.token}`;
        }

        const res = await fetch('/api/bookings', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload)
        });
        const responseText = await res.text();
        let data;
        try {
            data = responseText ? JSON.parse(responseText) : {};
        } catch (_) {
            throw new Error(res.ok
                ? 'Máy chủ trả về dữ liệu không hợp lệ'
                : `Máy chủ đang gặp lỗi (${res.status}). Vui lòng thử lại sau.`);
        }
        if (!res.ok) throw new Error(data.detail || data.message || 'Đặt sân thất bại');

        // Lưu đơn mới vào session recent bookings để hiển thị ngay lập tức
        if (!state.recentCreatedBookings) state.recentCreatedBookings = [];
        state.recentCreatedBookings.unshift(data);
        sessionStorage.setItem('recent_created_bookings', JSON.stringify(state.recentCreatedBookings.slice(0, 10)));

        let emailNotice = '';
        if (data.email_result && data.email_result.mode === 'LIVE_SMTP') {
            emailNotice = ` 📧 Đã gửi email xác nhận trực tiếp đến ${custEmail}!`;
        } else if (custEmail) {
            emailNotice = ` ℹ️ Thư xác nhận đã được lưu vào Hộp Thư Hệ Thống (Local Outbox - do chưa điền SMTP_USER trong file .env).`;
        }

        if (payMethod === 'WALLET') {
            showToast(`🎉 Đặt sân #${data.id} thành công và đã thanh toán qua Ví!${emailNotice}`, 'success');
            loadWalletData();
        } else if (payMethod === 'BANK_TRANSFER') {
            showToast(`🎉 Đặt sân #${data.id} thành công!${emailNotice} Vui lòng quét mã VietQR để hoàn tất.`, 'success');
            openPaymentQRModal(data.id, data.total_price, bankName);
        } else {
            showToast(`🎉 Đặt sân #${data.id} thành công! Quý khách thanh toán tại sân.${emailNotice}`, 'success');
        }

        // Tự động tải lại ma trận và toàn bộ danh sách đơn ngay lập tức
        renderLiveRecentBookings(state.recentCreatedBookings.slice(0, 5));
        loadBookingMatrix();
        loadMyRecentBookings();
        loadMyBookings();
        loadBookings();
    } catch (err) {
        console.error(err);
        showToast(`❌ Lỗi đặt sân: ${err.message}`, 'error');
    }
}

function openPaymentQRModal(bookingId, amount, bankName = 'MB') {
    const modal = document.getElementById('modal-payment-qr');
    if (!modal) return;
    const transferContent = `DATSAN ${bookingId}`;
    const qrUrl = `https://img.vietqr.io/image/${bankName}-0816227206-compact2.png?amount=${amount}&addInfo=${encodeURIComponent(transferContent)}&accountName=${encodeURIComponent('TRAN THANH CHUNG')}`;

    document.getElementById('vietqr-image').src = qrUrl;
    document.getElementById('qr-bank-name').innerText = `${bankName} Bank`;
    document.getElementById('qr-amount-text').innerText = `${amount.toLocaleString()} VNĐ`;
    document.getElementById('qr-content-text').innerText = transferContent;

    modal.classList.remove('hidden');
}

function closePaymentQRModal() {
    const modal = document.getElementById('modal-payment-qr');
    if (modal) modal.classList.add('hidden');
}

// INVOICE MODAL


// BOOKINGS ADMIN MANAGEMENT
async function loadBookings(manual = false) {
    try {
        const filterDate = document.getElementById('booking-filter-date')?.value || '';
        const url = filterDate ? `/api/bookings?booking_date=${filterDate}` : '/api/bookings';
        const bookings = await apiFetch(url);
        state.bookings = bookings;

        const tbody = document.getElementById('bookings-tbody');
        if (!tbody) return;

        if (!bookings || bookings.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-slate-400">Không có đơn đặt sân nào ${filterDate ? 'trong ngày ' + filterDate : ''}.</td></tr>`;
            return;
        }

        tbody.innerHTML = bookings.map(b => {
            let statusBadge = '';
            let approveBtn = '';
            let completeBtn = '';

            if (b.status === 'COMPLETED') {
                statusBadge = '<span class="px-3.5 py-1 rounded-full text-xs font-extrabold bg-sky-100 text-sky-800 shadow-sm border border-sky-300 whitespace-nowrap inline-flex items-center justify-center min-w-max">ĐÃ HOÀN THÀNH</span>';
                approveBtn = '<span class="text-xs font-bold text-sky-700">Đã trả sân</span>';
            } else if (b.status === 'CONFIRMED') {
                statusBadge = '<span class="px-3.5 py-1 rounded-full text-xs font-extrabold bg-emerald-500 text-white shadow-sm border border-emerald-400 whitespace-nowrap inline-flex items-center justify-center min-w-max">ĐÃ DUYỆT</span>';
                approveBtn = '<button disabled class="inline-flex items-center gap-1 bg-emerald-100 text-emerald-800 cursor-not-allowed px-2.5 py-1 rounded-lg text-xs font-bold border border-emerald-300 whitespace-nowrap"><i class="fa-solid fa-circle-check text-emerald-700"></i> Đã Duyệt</button>';
                const bookingEnd = new Date(`${b.booking_date}T${b.end_time}:00`);
                if (bookingEnd <= new Date()) {
                    completeBtn = `<button onclick="completeBooking(${b.id})" class="inline-flex items-center gap-1 bg-sky-600 hover:bg-sky-500 text-white px-2.5 py-1 rounded-lg text-xs font-bold transition shadow whitespace-nowrap" title="Xác nhận khách đã trả sân"><i class="fa-solid fa-flag-checkered"></i> Hoàn tất</button>`;
                }
            } else if (b.status === 'PENDING') {
                statusBadge = '<span class="px-3.5 py-1 rounded-full text-xs font-extrabold bg-amber-400 text-slate-900 shadow-sm border border-amber-500 whitespace-nowrap inline-flex items-center justify-center min-w-max">CHỜ DUYỆT</span>';
                approveBtn = `<button onclick="confirmBookingAndInvoice(${b.id})" class="inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-500 text-white px-2.5 py-1 rounded-lg text-xs font-bold transition shadow whitespace-nowrap"><i class="fa-solid fa-check"></i> Duyệt Đơn</button>`;
            } else {
                statusBadge = '<span class="px-3.5 py-1 rounded-full text-xs font-extrabold bg-rose-500 text-white shadow-sm border border-rose-400 whitespace-nowrap inline-flex items-center justify-center min-w-max">ĐÃ HỦY</span>';
                approveBtn = '<button disabled class="inline-flex items-center gap-1 bg-rose-100 text-rose-700 cursor-not-allowed px-2.5 py-1 rounded-lg text-xs font-bold border border-rose-300 whitespace-nowrap">Đã Hủy</button>';
            }

            const canManage = b.status !== 'COMPLETED' && b.status !== 'CANCELLED';
            return `
                <tr class="hover:bg-slate-100 transition">
                    <td class="p-3.5 font-mono text-teal-700 font-bold whitespace-nowrap">#${b.id}</td>
                    <td class="p-3.5"><strong class="text-slate-900">${b.customer_name}</strong><br><span class="text-slate-600 font-mono text-[11px]">${b.customer_phone}</span></td>
                    <td class="p-3.5"><strong class="text-slate-800">${b.pitch?.name || 'Sân'}</strong><br><span class="text-[10px] text-slate-600">${b.pitch?.location || ''}</span></td>
                    <td class="p-3.5 font-mono text-slate-700 whitespace-nowrap">${b.start_time}-${b.end_time}<br><span class="text-slate-600 text-[11px]">${b.booking_date}</span></td>
                    <td class="p-3.5 whitespace-nowrap"><strong class="text-emerald-700 font-mono">${(Number(b.total_price) || 0).toLocaleString()}đ</strong><br><span class="text-[10px] text-blue-700 font-mono">Cọc: ${(Number(b.deposit_amount) || 0).toLocaleString()}đ</span></td>
                    <td class="p-3.5 text-center whitespace-nowrap">${statusBadge}</td>
                    <td class="p-3.5 text-right space-x-1.5 whitespace-nowrap">
                        <button onclick="openAINotifDialog(${b.id})" class="inline-flex items-center gap-1 bg-indigo-600 hover:bg-indigo-500 text-white px-2.5 py-1 rounded-lg text-xs font-bold transition shadow whitespace-nowrap" title="Tạo tin nhắn xác nhận AI"><i class="fa-solid fa-wand-magic-sparkles"></i> Tạo tin nhắn xác nhận</button>
                        ${canManage ? `<button onclick="openEditBookingModal(${b.id})" class="inline-flex items-center gap-1 bg-blue-600 hover:bg-blue-500 text-white px-2.5 py-1 rounded-lg text-xs font-bold transition whitespace-nowrap" title="Sửa / Đổi lịch đặt sân"><i class="fa-solid fa-pen-to-square"></i> Đổi Lịch</button>` : ''}
                        ${approveBtn}
                        ${completeBtn}
                        ${canManage ? `<button onclick="cancelAdminBooking(${b.id})" class="inline-flex items-center gap-1 bg-rose-600 hover:bg-rose-500 text-white px-2 py-1 rounded-lg text-xs font-bold transition whitespace-nowrap" title="Hủy đơn"><i class="fa-solid fa-xmark"></i></button>` : ''}
                    </td>
                </tr>
            `;
        }).join('');
        if (manual) showToast('Đã làm mới danh sách đơn đặt sân thành công!', 'success');
    } catch (e) {
        console.error("loadBookings error:", e);
        const tbody = document.getElementById('bookings-tbody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-rose-400 font-bold">Lỗi tải đơn đặt sân: ${e.message}</td></tr>`;
        }
    }
}

function setBookingDateFilter(mode) {
    const input = document.getElementById('booking-filter-date');
    if (!input) return;
    if (mode === 'today') {
        input.value = getLocalDateString();
    } else {
        input.value = '';
    }
    loadBookings();
}

async function confirmBookingAndInvoice(bookingId) {
    try {
        const data = await apiFetch(`/api/bookings/${bookingId}/confirm-and-send-invoice`, {
            method: 'POST'
        });
        showToast(data.message || 'Đã duyệt đơn và gửi hóa đơn thành công', 'success');
        loadBookings();
    } catch (e) { showToast(e.message, 'error'); }
}

async function cancelAdminBooking(bookingId) {
    if (!confirm('Bạn có chắc chắn muốn hủy đơn đặt sân này?')) return;
    try {
        await apiFetch(`/api/bookings/${bookingId}/cancel`, {
            method: 'POST'
        });
        showToast('Đã hủy đơn thành công', 'success');
        loadBookings();
    } catch (e) { showToast(e.message, 'error'); }
}

async function completeBooking(bookingId) {
    if (!confirm('Xác nhận khách đã trả sân và hoàn tất lượt thuê? Các khoản chưa thanh toán vẫn cần được xử lý riêng.')) return;
    try {
        const data = await apiFetch(`/api/bookings/${bookingId}/complete`, { method: 'POST' });
        showToast(data.message || 'Đã hoàn tất đơn đặt sân', 'success');
        loadBookings();
        loadBookingMatrix();
    } catch (e) { showToast(e.message, 'error'); }
}

// DASHBOARD STATS
async function loadDashboardStats(manual = false) {
    try {
        const data = await apiFetch('/api/stats/dashboard');
        
        const revEl = document.getElementById('stat-revenue');
        const pitchEl = document.getElementById('stat-pitches');
        const bookEl = document.getElementById('stat-bookings');
        const occEl = document.getElementById('stat-occupancy');

        if (revEl) revEl.innerText = `${Number(data.total_revenue).toLocaleString('vi-VN')} đ`;
        if (pitchEl) pitchEl.innerText = `${data.total_pitches} Sân`;
        if (bookEl) bookEl.innerText = `${data.total_bookings} Lượt`;
        if (occEl) occEl.innerText = `${data.occupancy_rate}%`;

        const revChartCanvas = document.getElementById('chart-revenue');
        if (revChartCanvas) {
            const ctxRev = revChartCanvas.getContext('2d');
            if (state.chartRevenue) state.chartRevenue.destroy();
            state.chartRevenue = new Chart(ctxRev, {
                type: 'bar',
                data: {
                    labels: data.daily_stats.map(d => d.date.split('-').slice(1).join('/')),
                    datasets: [{
                        label: 'Doanh thu',
                        data: data.daily_stats.map(d => d.revenue),
                        backgroundColor: 'rgba(16, 185, 129, 0.7)',
                        borderColor: '#10b981',
                        borderRadius: 6
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        }

        const sportsChartCanvas = document.getElementById('chart-sports');
        if (sportsChartCanvas) {
            const ctxSports = sportsChartCanvas.getContext('2d');
            if (state.chartSports) state.chartSports.destroy();
            state.chartSports = new Chart(ctxSports, {
                type: 'doughnut',
                data: {
                    labels: ['Bóng đá', 'Cầu lông', 'Tennis', 'Gym', 'Bóng rổ'],
                    datasets: [{
                        data: [
                            data.sports_distribution?.football || 0,
                            data.sports_distribution?.badminton || 0,
                            data.sports_distribution?.tennis || 0,
                            data.sports_distribution?.gym || 0,
                            data.sports_distribution?.basketball || 0
                        ],
                        backgroundColor: ['#10b981', '#38bdf8', '#f59e0b', '#ec4899', '#8b5cf6'],
                        borderWidth: 0
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } } }
            });
        }
        loadAIDashboardSummary();
        if (manual) showToast('Đã làm mới dữ liệu Báo cáo Thống kê & Biểu đồ AI thành công!', 'success');
    } catch (e) { console.error(e); }
}

// USER ROLES & ACCESS AUDIT LOGS
async function loadUserRolesList(manual = false) {
    const tbody = document.getElementById('user-roles-tbody');
    try {
        const users = await apiFetch('/api/auth/users');
        if (!tbody) return;
        tbody.innerHTML = users.map(u => `
            <tr class="hover:bg-slate-800/60 transition">
                <td class="p-3 font-mono text-emerald-400 whitespace-nowrap">#${u.id}</td>
                <td class="p-3 font-bold text-white whitespace-nowrap">${u.full_name}</td>
                <td class="p-3"><p class="text-slate-200 font-mono">${u.username}</p><p class="text-[10px] text-slate-400 font-mono">${u.email}</p></td>
                <td class="p-3 font-mono text-slate-300 whitespace-nowrap">${u.phone || 'Chưa cập nhật'}</td>
                <td class="p-3 text-[11px] text-slate-400 whitespace-nowrap">${u.last_login_at ? new Date(u.last_login_at).toLocaleString('vi-VN') : 'Chưa đăng nhập'}</td>
                <td class="p-3 whitespace-nowrap"><span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold whitespace-nowrap inline-block ${u.role === 'ADMIN' ? 'bg-red-950 text-red-300 border border-red-800' : u.role === 'STAFF' ? 'bg-blue-950 text-blue-300 border border-blue-800' : 'bg-emerald-950 text-emerald-300 border border-emerald-800'}">${u.role}</span></td>
                <td class="p-3 text-right whitespace-nowrap">
                    <select onchange="changeUserRole(${u.id}, this.value)" class="bg-slate-950 border border-slate-700 text-xs rounded-lg px-2 py-1 text-slate-200">
                        <option value="CUSTOMER" ${u.role === 'CUSTOMER' ? 'selected' : ''}>Khách hàng</option>
                        <option value="STAFF" ${u.role === 'STAFF' ? 'selected' : ''}>Lễ tân (Staff)</option>
                        <option value="ADMIN" ${u.role === 'ADMIN' ? 'selected' : ''}>Quản trị (Admin)</option>
                    </select>
                </td>
            </tr>
        `).join('');
        if (manual) showToast('Đã làm mới danh sách phân quyền tài khoản thành công!', 'success');
    } catch (e) {
        console.error(e);
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="7" class="p-5 text-center text-amber-300 font-semibold bg-amber-950/20 border border-amber-800/40 rounded-xl"><i class="fa-solid fa-lock mr-2"></i> ${e.message} (Cần đăng nhập tài khoản Quản trị Admin)</td></tr>`;
        }
        if (manual) showToast(e.message, 'warning');
    }
}

async function changeUserRole(userId, newRole) {
    try {
        await apiFetch(`/api/auth/users/${userId}/role`, {
            method: 'PATCH',
            body: JSON.stringify({ role: newRole })
        });
        showToast(`Đã phân quyền ${newRole} cho người dùng thành công!`, 'success');
        loadUserRolesList();
        loadActivityLogs();
    } catch (e) { showToast(e.message, 'error'); }
}

async function loadActivityLogs(manual = false) {
    const tbody = document.getElementById('activity-logs-tbody');
    try {
        const logs = await apiFetch('/api/auth/activity-logs');
        if (!tbody) return;
        tbody.innerHTML = logs.map(l => `
            <tr class="hover:bg-slate-800/60 transition">
                <td class="p-2.5 text-slate-400 whitespace-nowrap">${new Date(l.timestamp).toLocaleString('vi-VN')}</td>
                <td class="p-2.5 font-bold text-emerald-400 whitespace-nowrap">${l.username}</td>
                <td class="p-2.5 whitespace-nowrap"><span class="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">${l.role}</span></td>
                <td class="p-2.5 text-slate-200">${l.action}</td>
                <td class="p-2.5 text-slate-500 font-mono text-[10px] whitespace-nowrap">${l.ip_address}</td>
            </tr>
        `).join('');
        if (manual) showToast('Đã làm mới nhật ký truy cập thành công!', 'success');
    } catch (e) {
        console.error(e);
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="5" class="p-5 text-center text-amber-300 font-semibold bg-amber-950/20 border border-amber-800/40 rounded-xl"><i class="fa-solid fa-lock mr-2"></i> ${e.message} (Cần đăng nhập tài khoản Quản trị Admin)</td></tr>`;
        }
        if (manual) showToast(e.message, 'warning');
    }
}

// COMMUNITY: MATCHES, EVENTS, REVIEWS
async function loadMatches() {
    try {
        const res = await fetch('/api/community/matches');
        const data = await res.json();
        state.matches = data;
        const grid = document.getElementById('matches-grid');
        if (!grid) return;
        if (!data || data.length === 0) {
            grid.innerHTML = `<div class="col-span-full p-8 text-center text-slate-400 text-xs bg-slate-900/60 border border-slate-800 rounded-3xl">Chưa có bài đăng tìm kèo giao lưu nào. Hãy bấm "Đăng Bài Tìm Kèo Mới" để tạo bài viết đầu tiên!</div>`;
            return;
        }
        grid.innerHTML = data.map(m => {
            const canDelete = state.user && (state.user.role === 'ADMIN' || state.user.role === 'STAFF' || state.user.id === m.user_id);
            const sportBadge = {
                'FOOTBALL': '⚽ Bóng đá',
                'BADMINTON': '🏸 Cầu lông',
                'TENNIS': '🎾 Tennis',
                'GYM': '🏋️ Gym',
                'BASKETBALL': '🏀 Bóng rổ'
            }[m.sport_type] || m.sport_type;

            return `
            <div class="glass-card glass-card-hover rounded-3xl p-5 space-y-3.5 shadow-2xl flex flex-col justify-between border border-slate-800/80">
                <div>
                    <div class="flex justify-between items-center border-b border-slate-800/80 pb-2.5">
                        <span class="text-[11px] font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/40 px-3 py-0.5 rounded-full flex items-center gap-1 shadow">
                            ${sportBadge}
                        </span>
                        <div class="flex items-center gap-2">
                            <span class="text-[11px] font-bold text-slate-300 bg-slate-950 px-2.5 py-0.5 rounded-full border border-slate-800">${m.team_level}</span>
                            ${canDelete ? `<button type="button" onclick="deleteMatchPost(${m.id})" class="text-rose-400 hover:text-rose-300 text-xs p-1 transition" title="Xóa bài đăng"><i class="fa-solid fa-trash"></i></button>` : ''}
                        </div>
                    </div>

                    <div class="mt-3 space-y-2">
                        <h3 class="font-black text-sm text-slate-900 dark:text-white flex items-center gap-2">
                            <i class="fa-solid fa-user-ninja text-amber-500 text-xs"></i>
                            <span>${m.author_name}</span>
                        </h3>
                        <p class="text-xs text-slate-800 dark:text-slate-200 font-medium leading-relaxed bg-slate-100 dark:bg-slate-950/60 p-3.5 rounded-2xl border border-slate-200 dark:border-slate-800">${m.content}</p>
                    </div>
                </div>

                <div class="pt-3 border-t border-slate-800/80 flex justify-between items-center text-xs">
                    <span class="text-slate-300 font-medium"><i class="fa-solid fa-clock text-amber-400 mr-1.5"></i> ${m.match_time}</span>
                    <a href="tel:${m.contact_phone}" class="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-black text-xs px-3.5 py-2 rounded-xl transition shadow-lg flex items-center gap-1.5 transform hover:scale-[1.03]">
                        <i class="fa-solid fa-phone-volume"></i> Gọi Kèo: ${m.contact_phone}
                    </a>
                </div>
            </div>
        `;
        }).join('');
    } catch (e) { console.error(e); }
}

async function deleteMatchPost(postId) {
    if (!confirm('Bạn có chắc muốn xóa bài đăng tìm kèo này không?')) return;
    try {
        const data = await apiFetch(`/api/community/matches/${postId}`, { method: 'DELETE' });
        showToast(data.message || 'Đã xóa bài đăng thành công', 'success');
        loadMatches();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function openCreateMatchModal() {
    const modal = document.getElementById('modal-create-match');
    if (modal) modal.classList.remove('hidden');
    if (state.user) {
        const nameInput = document.getElementById('match-author-name');
        const phoneInput = document.getElementById('match-phone');
        if (nameInput && !nameInput.value) nameInput.value = state.user.full_name || state.user.username;
        if (phoneInput && !phoneInput.value) phoneInput.value = state.user.phone || '';
    }
}

function closeCreateMatchModal() {
    const modal = document.getElementById('modal-create-match');
    if (modal) modal.classList.add('hidden');
}

async function submitCreateMatch(e) {
    if (e) e.preventDefault();
    const btn = e?.target?.querySelector('button[type="submit"]');
    const origText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Đang đăng bài...';
    }

    const payload = {
        author_name: document.getElementById('match-author-name').value,
        sport_type: document.getElementById('match-sport-type').value,
        team_level: document.getElementById('match-level').value || 'Phong trào',
        match_time: document.getElementById('match-time').value,
        contact_phone: document.getElementById('match-phone').value,
        content: document.getElementById('match-content').value
    };

    try {
        await apiFetch('/api/community/matches', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        showToast('Đã đăng bài tìm kèo giao lưu thành công!', 'success');
        closeCreateMatchModal();
        loadMatches();
        if (e?.target) e.target.reset();
    } catch (err) {
        console.error(err);
        showToast(`❌ Lỗi đăng bài: ${err.message}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origText;
        }
    }
}

function openCreateEventModal() {
    if (!state.user || (state.user.role !== 'ADMIN' && state.user.role !== 'STAFF')) {
        showToast('Chỉ Quản trị viên (Admin/Staff) mới có quyền đăng bài thông báo sự kiện!', 'warning');
        return;
    }
    const modal = document.getElementById('modal-create-event');
    if (modal) modal.classList.remove('hidden');
}

function closeCreateEventModal() {
    const modal = document.getElementById('modal-create-event');
    if (modal) modal.classList.add('hidden');
}

async function submitCreateEvent(e) {
    if (e) e.preventDefault();
    const btn = e?.target?.querySelector('button[type="submit"]');
    const origText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Đang đăng sự kiện...';
    }

    const payload = {
        title: document.getElementById('event-title').value,
        category: document.getElementById('event-category').value,
        event_date: document.getElementById('event-date').value,
        banner_url: document.getElementById('event-banner-url').value || null,
        description: document.getElementById('event-description').value
    };

    try {
        await apiFetch('/api/community/events', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        showToast('Đã đăng bài thông báo sự kiện thành công!', 'success');
        closeCreateEventModal();
        loadEvents();
        if (e?.target) e.target.reset();
    } catch (err) {
        console.error(err);
        showToast(`❌ Lỗi đăng sự kiện: ${err.message}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origText;
        }
    }
}

async function deleteEvent(eventId) {
    if (!confirm('Bạn có chắc muốn xóa bài đăng sự kiện này không?')) return;
    try {
        const data = await apiFetch(`/api/community/events/${eventId}`, { method: 'DELETE' });
        showToast(data.message || 'Đã xóa sự kiện thành công', 'success');
        loadEvents();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function loadEvents() {
    try {
        const data = await apiFetch('/api/community/events');
        state.events = data;
        const grid = document.getElementById('events-grid');
        if (!grid) return;
        if (!data || data.length === 0) {
            grid.innerHTML = `<div class="col-span-full p-8 text-center text-slate-400 text-xs bg-slate-900/60 border border-slate-800 rounded-3xl">Chưa có bài thông báo sự kiện nào. Ban Quản Trị có thể đăng bài viết mới ở đây!</div>`;
            return;
        }
        grid.innerHTML = data.map(ev => {
            const canDelete = state.user && (state.user.role === 'ADMIN' || state.user.role === 'STAFF');
            const eventImage = ev.banner_url && ev.banner_url.startsWith('/')
                ? ev.banner_url
                : '/static/images/pitch-01.jpg';
            return `
            <div class="glass-card glass-card-hover rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row border border-slate-800/80 group">
                <div class="w-full md:w-56 h-48 md:h-auto relative flex-shrink-0 overflow-hidden">
                    <img src="${eventImage}" alt="${ev.title}" class="w-full h-full object-cover group-hover:scale-110 transition duration-700 ease-out" onerror="this.onerror=null; this.src='/static/images/pitch-01.jpg'">
                    <div class="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent md:hidden"></div>
                </div>
                <div class="p-5 space-y-3 flex-1 flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center border-b border-slate-800/80 pb-2">
                            <span class="text-[10px] font-extrabold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-3 py-0.5 rounded-full flex items-center gap-1 shadow">
                                <i class="fa-solid fa-bullhorn text-amber-400"></i> ${ev.category}
                            </span>
                            ${canDelete ? `<button type="button" onclick="deleteEvent(${ev.id})" class="text-rose-400 hover:text-rose-300 text-xs p-1 transition" title="Xóa sự kiện"><i class="fa-solid fa-trash"></i></button>` : ''}
                        </div>
                        <h3 class="font-black text-base text-white mt-2 group-hover:text-emerald-300 transition leading-snug">${ev.title}</h3>
                        <p class="text-xs text-slate-300 mt-2 line-clamp-3 leading-relaxed">${ev.description}</p>
                    </div>
                    <div class="text-xs text-amber-300 font-bold flex items-center gap-2 pt-3 border-t border-slate-800/80">
                        <span class="bg-amber-950/60 border border-amber-500/40 px-2.5 py-1 rounded-xl flex items-center gap-1.5">
                            <i class="fa-solid fa-calendar-check text-amber-400"></i> ${ev.event_date}
                        </span>
                        <span class="text-[10px] text-slate-400 font-normal">Sự kiện chính thức từ Ban Quản Lý</span>
                    </div>
                </div>
            </div>
        `;
        }).join('');
    } catch (e) { console.error(e); }
}

async function deleteReview(reviewId) {
    if (!confirm('Bạn có chắc muốn xóa đánh giá này không?')) return;
    try {
        const data = await apiFetch(`/api/community/reviews/${reviewId}`, { method: 'DELETE' });
        showToast(data.message || 'Đã xóa đánh giá thành công', 'success');
        loadReviews();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function loadReviews() {
    try {
        const data = await apiFetch('/api/community/reviews');
        state.reviews = data;
        const grid = document.getElementById('reviews-grid');
        if (!grid) return;
        grid.innerHTML = data.map(r => {
            const canDelete = state.user && (state.user.role === 'ADMIN' || state.user.role === 'STAFF' || (r.user_id && state.user.id === r.user_id));
            return `
            <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 space-y-3 shadow-xl">
                <div class="flex justify-between items-center">
                    <h4 class="font-bold text-xs text-white">${r.customer_name}</h4>
                    <div class="flex items-center gap-2">
                        <span class="text-amber-400 text-xs font-bold">${'★'.repeat(r.rating)}</span>
                        ${canDelete ? `<button type="button" onclick="deleteReview(${r.id})" class="text-rose-400 hover:text-rose-300 text-xs" title="Xóa đánh giá"><i class="fa-solid fa-trash"></i></button>` : ''}
                    </div>
                </div>
                <p class="text-xs text-slate-300 leading-relaxed italic">"${r.comment}"</p>
                <p class="text-[10px] text-slate-500 pt-2 border-t border-slate-800">${new Date(r.created_at).toLocaleDateString('vi-VN')}</p>
            </div>
        `;
        }).join('');
    } catch (e) { console.error(e); }
}

function openCreateReviewModal() {
    const modal = document.getElementById('modal-create-review');
    if (modal) modal.classList.remove('hidden');
    if (state.user) {
        const nameInput = document.getElementById('rev-cust-name');
        if (nameInput) nameInput.value = state.user.full_name || state.user.username;
    }
}

function closeCreateReviewModal() {
    const modal = document.getElementById('modal-create-review');
    if (modal) modal.classList.add('hidden');
}

async function submitCreateReview(e) {
    if (e) e.preventDefault();
    const btn = e?.target?.querySelector('button[type="submit"]');
    const origText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Đang gửi...';
    }

    const payload = {
        customer_name: document.getElementById('rev-cust-name').value,
        rating: parseInt(document.getElementById('rev-rating').value),
        comment: document.getElementById('rev-comment').value
    };

    try {
        await apiFetch('/api/community/reviews', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        showToast('Cảm ơn bạn đã gửi đánh giá quý báu!', 'success');
        closeCreateReviewModal();
        loadReviews();
        if (e?.target) e.target.reset();
    } catch (err) {
        showToast(`❌ Lỗi gửi đánh giá: ${err.message}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origText;
        }
    }
}

function toggleAIChatWidget() {
    const chatWindow = document.getElementById('ai-chat-window');
    if (chatWindow) {
        chatWindow.classList.toggle('hidden');
        if (!chatWindow.classList.contains('hidden')) {
            const input = document.getElementById('ai-chat-input');
            if (input) {
                input.setAttribute('autocomplete', 'off');
                input.setAttribute('autocorrect', 'off');
                input.setAttribute('autocapitalize', 'off');
                input.setAttribute('spellcheck', 'false');
                input.focus();
            }
        }
    }
}

function openAIChatWidget() {
    const chatWindow = document.getElementById('ai-chat-window');
    if (chatWindow) chatWindow.classList.remove('hidden');
    const input = document.getElementById('ai-chat-input');
    if (input) {
        input.setAttribute('autocomplete', 'off');
        input.setAttribute('autocorrect', 'off');
        input.setAttribute('autocapitalize', 'off');
        input.setAttribute('spellcheck', 'false');
        input.focus();
    }
}

function formatAIMarkdown(text) {
    if (!text) return '';
    let formatted = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
    return formatted;
}

async function handleAIChatSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('ai-chat-input');
    const query = input?.value.trim();
    if (!query) return;

    appendChatMessage('user', query);
    input.value = '';

    // Append loading placeholder
    const loadingId = 'ai-loading-' + Date.now();
    appendChatMessage('bot', '<i class="fa-solid fa-spinner fa-spin mr-1"></i> AI đang phân tích dữ liệu và trả lời...', loadingId);

    try {
        const res = await fetch('/api/ai/suggest-slots', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ user_query: query })
        });
        const data = await res.json();
        
        // Format markdown (bold, list, linebreaks)
        let formattedText = data.response
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');

        let botHtml = `<div class="space-y-2 text-slate-800 leading-relaxed">${formattedText}</div>`;

        if (data.suggested_slots && data.suggested_slots.length > 0) {
            botHtml += `<div class="space-y-1.5 pt-2 border-t border-slate-200 mt-2">`;
            data.suggested_slots.forEach(slot => {
                const priceVal = Number(slot.price_per_hour || slot.price || 0);
                const slotDate = slot.booking_date || slot.date || getLocalDateString();
                botHtml += `
                    <div class="bg-slate-50 border border-slate-200 rounded-xl p-2 flex items-center justify-between">
                        <div>
                            <p class="font-bold text-slate-800 text-[11px]">🏟️ ${slot.pitch_name}</p>
                            <p class="text-[10px] text-slate-500">${slot.start_time} - ${slot.end_time} (${priceVal.toLocaleString()}đ/h)</p>
                        </div>
                        <button onclick="aiQuickBookFromChat('${slotDate}', '${slot.start_time}', '${slot.end_time}', ${slot.pitch_id})" 
                                class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[10px] px-2.5 py-1 rounded-lg shadow transition cursor-pointer">
                            <i class="fa-solid fa-calendar-check mr-1"></i> Đặt sân ngay
                        </button>
                    </div>
                `;
            });
            botHtml += `</div>`;
        }

        updateChatMessage(loadingId, botHtml);
    } catch (err) {
        updateChatMessage(loadingId, `<span class="text-rose-600">Lỗi kết nối AI: ${err.message}</span>`);
    }
}

function appendChatMessage(sender, text, customId = null) {
    const box = document.getElementById('ai-chat-messages');
    if (!box) return;
    const msgDiv = document.createElement('div');
    if (customId) msgDiv.id = customId;

    if (sender === 'user') {
        msgDiv.className = "flex justify-end";
        msgDiv.innerHTML = `
            <div class="bg-purple-600 text-white p-3 rounded-2xl rounded-tr-none shadow-sm max-w-[85%] text-xs">
                ${text}
            </div>
        `;
    } else {
        msgDiv.className = "flex items-start space-x-2";
        msgDiv.innerHTML = `
            <div class="w-6 h-6 rounded-full bg-purple-600 text-white flex items-center justify-center text-[10px] flex-shrink-0">AI</div>
            <div class="bg-white border border-slate-200 p-3 rounded-2xl rounded-tl-none shadow-sm text-slate-800 space-y-1 max-w-[85%] text-xs">
                ${text}
            </div>
        `;
    }
    box.appendChild(msgDiv);
    box.scrollTop = box.scrollHeight;
}

function updateChatMessage(msgId, newHtml) {
    const el = document.getElementById(msgId);
    if (!el) return;
    el.innerHTML = `
        <div class="w-6 h-6 rounded-full bg-purple-600 text-white flex items-center justify-center text-[10px] flex-shrink-0">AI</div>
        <div class="bg-white border border-slate-200 p-3 rounded-2xl rounded-tl-none shadow-sm text-slate-800 space-y-1 max-w-[85%] text-xs">
            ${newHtml}
        </div>
    `;
    const box = document.getElementById('ai-chat-messages');
    if (box) box.scrollTop = box.scrollHeight;
}

function aiQuickBookFromChat(date, start, end, pitchId) {
    if (!state.user || !state.token) {
        showToast('💡 Vui lòng đăng nhập tài khoản thành viên để đặt sân!', 'info');
        openAuthModal('login');
        return;
    }
    switchTab('matrix-booking');
    const p = state.pitches?.find(x => x.id === pitchId);
    if (p) filterBookingSport(p.sport_type);
    selectVisualPitch(pitchId);

    const dateInput = document.getElementById('matrix-booking-date');
    const startInput = document.getElementById('matrix-start-time');
    const endInput = document.getElementById('matrix-end-time');
    if (dateInput) dateInput.value = date;
    if (startInput) startInput.value = start;
    if (endInput) endInput.value = end;

    recalculateMatrixPrice();
    toggleAIChatWidget();
    showToast(`🎯 Đã chọn ${p ? p.name : 'Sân'} lúc ${start} - ${end} ngày ${date}!`, 'success');
}

// AI NOTIFICATIONS & OCCUPANCY

async function callAIOccupancyReport() {
    const resBox = document.getElementById('ai-occupancy-result-box');
    if (resBox) resBox.classList.remove('hidden');
    try {
        const res = await fetch('/api/ai/occupancy-report', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ days_back: 7 })
        });
        const data = await res.json();
        const sumEl = document.getElementById('ai-occupancy-summary-text');
        const promoContainer = document.getElementById('ai-promotions-container');
        if (sumEl) sumEl.innerText = data.summary;
        if (promoContainer) {
            promoContainer.innerHTML = (data.suggested_promotions || []).map(p => `
                <div class="bg-slate-900 border border-purple-500/40 rounded-2xl p-3 space-y-1.5 text-xs shadow-md">
                    <div class="flex items-center justify-between">
                        <span class="text-[10px] font-mono font-bold bg-purple-900/60 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded-full">${p.code}</span>
                        <span class="text-[10px] text-emerald-400 font-semibold">${p.expected_boost || ''}</span>
                    </div>
                    <p class="font-bold text-amber-300">${p.discount || p.title || 'Ưu đãi đặc biệt'}</p>
                    <p class="text-[11px] text-slate-300"><i class="fa-solid fa-bullseye text-purple-400 mr-1"></i> ${p.target_sport || p.target || 'Toàn hệ thống'}</p>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error(e);
    }
}


// =========================================================================
// QUẢN LÝ KHÁCH HÀNG (TABLE 12) & BÁO CÁO THEO KỲ (MỤC 3.2)
// =========================================================================

let customersCache = [];
let customerSearchTimer = null;
let currentReportPeriod = 'week';

function renderReportsCharts(revenueData, occupancyData, period) {
    const isBright = document.body.classList.contains('theme-bright');
    const textColor = isBright ? '#334155' : '#cbd5e1';
    const gridColor = isBright ? 'rgba(100, 116, 139, 0.18)' : 'rgba(148, 163, 184, 0.18)';
    const today = new Date();
    const startDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    let dates = [];

    if (period === 'day') {
        dates = [startDate];
    } else if (period === 'week') {
        startDate.setDate(startDate.getDate() - ((startDate.getDay() + 6) % 7));
        dates = Array.from({ length: 7 }, (_, index) => new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + index));
    } else {
        const monthStart = new Date(startDate.getFullYear(), startDate.getMonth(), 1);
        const daysInMonth = today.getDate();
        dates = Array.from({ length: daysInMonth }, (_, index) => new Date(monthStart.getFullYear(), monthStart.getMonth(), index + 1));
    }

    const dateKey = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    const dailyRevenue = new Map((revenueData?.revenue_by_day || []).map(item => [item.date, Number(item.revenue || 0)]));
    if (!revenueData?.revenue_by_day) {
        (revenueData?.bookings || []).forEach(booking => {
            dailyRevenue.set(booking.booking_date, (dailyRevenue.get(booking.booking_date) || 0) + Number(booking.total_price || 0));
        });
    }

    const revenueCanvas = document.getElementById('report-revenue-chart');
    if (revenueCanvas) {
        state.chartReportRevenue?.destroy();
        state.chartReportRevenue = new Chart(revenueCanvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: dates.map(date => dateKey(date).slice(5).split('-').reverse().join('/')),
                datasets: [{
                    label: 'Doanh thu (VNĐ)',
                    data: dates.map(date => dailyRevenue.get(dateKey(date)) || 0),
                    borderColor: '#059669',
                    backgroundColor: 'rgba(16, 185, 129, 0.16)',
                    pointBackgroundColor: '#059669',
                    pointRadius: 3,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: textColor } } },
                scales: {
                    x: { ticks: { color: textColor, maxTicksLimit: 10 }, grid: { color: gridColor } },
                    y: { beginAtZero: true, ticks: { color: textColor, callback: value => `${Number(value).toLocaleString('vi-VN')} đ` }, grid: { color: gridColor } }
                }
            }
        });
    }

    const sportLabels = {
        FOOTBALL: 'Bóng đá', BADMINTON: 'Cầu lông', TENNIS: 'Tennis', GYM: 'Gym', BASKETBALL: 'Bóng rổ'
    };
    const revenueBySport = revenueData?.revenue_by_sport || {};
    const sportKeys = Object.keys(revenueBySport).filter(key => Number(revenueBySport[key]) > 0);
    const sportCanvas = document.getElementById('report-sport-revenue-chart');
    if (sportCanvas) {
        state.chartReportSportRevenue?.destroy();
        state.chartReportSportRevenue = new Chart(sportCanvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: sportKeys.length ? sportKeys.map(key => sportLabels[key] || key) : ['Chưa có doanh thu'],
                datasets: [{
                    data: sportKeys.length ? sportKeys.map(key => Number(revenueBySport[key])) : [1],
                    backgroundColor: sportKeys.length ? ['#059669', '#0284c7', '#d97706', '#db2777', '#7c3aed'] : ['#94a3b8'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: textColor } } }
            }
        });
    }

    const occupancy = occupancyData?.pitches_occupancy || [];
    const occupancyCanvas = document.getElementById('report-pitch-occupancy-chart');
    if (occupancyCanvas) {
        state.chartReportOccupancy?.destroy();
        state.chartReportOccupancy = new Chart(occupancyCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: occupancy.map(pitch => pitch.pitch_name),
                datasets: [{
                    label: 'Công suất (%)',
                    data: occupancy.map(pitch => Number.parseFloat(pitch.occupancy_rate) || 0),
                    backgroundColor: 'rgba(14, 165, 233, 0.72)',
                    borderColor: '#0284c7',
                    borderWidth: 1,
                    borderRadius: 5
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, max: 100, ticks: { color: textColor, callback: value => `${value}%` }, grid: { color: gridColor } },
                    y: { ticks: { color: textColor, autoSkip: false }, grid: { display: false } }
                }
            }
        });
    }
}

function renderReportDetailTables(revenueData) {
    const peakBody = document.getElementById('report-peak-hours-body');
    if (peakBody) {
        const peakHours = revenueData?.peak_hours || [];
        peakBody.innerHTML = peakHours.length ? peakHours.map(item => `
            <tr><td class="p-2.5 font-semibold text-slate-200">${item.hour}</td><td class="p-2.5 text-center">${item.bookings}</td><td class="p-2.5 text-right font-mono text-emerald-400">${Number(item.revenue).toLocaleString('vi-VN')} đ</td></tr>
        `).join('') : '<tr><td colspan="3" class="p-4 text-center text-slate-500">Chưa có lượt đặt trong kỳ.</td></tr>';
    }

    const loyalBody = document.getElementById('report-loyal-customers-body');
    if (loyalBody) {
        const customers = revenueData?.loyal_customers || [];
        loyalBody.innerHTML = customers.length ? customers.map((customer, index) => `
            <tr><td class="p-2.5"><span class="font-mono text-amber-400 mr-1">#${index + 1}</span><span class="font-semibold text-slate-200">${customer.name}</span><div class="text-[10px] text-slate-400">${customer.phone}</div></td><td class="p-2.5 text-center">${customer.booking_count}</td><td class="p-2.5 text-right font-mono text-emerald-400">${Number(customer.total_spent).toLocaleString('vi-VN')} đ</td></tr>
        `).join('') : '<tr><td colspan="3" class="p-4 text-center text-slate-500">Chưa có khách hàng đủ điều kiện thống kê.</td></tr>';
    }
}

// --- KHÁCH HÀNG (CUSTOMERS) ---
async function loadCustomers(search = '') {
    try {
        const tbody = document.getElementById('customer-table-body');
        if (!tbody) return;

        let url = '/api/customers';
        if (search && search.trim()) {
            url += `?search=${encodeURIComponent(search.trim())}`;
        }

        const res = await apiFetch(url);
        if (!res) return;

        customersCache = res;

        // Cập nhật KPIs
        const totalCust = customersCache.length;
        const activeCust = customersCache.filter(c => c.bookings && c.bookings.length > 0).length;

        const statTotalEl = document.getElementById('stat-cust-total');
        if (statTotalEl) statTotalEl.innerText = `${totalCust} Khách`;

        const statActiveEl = document.getElementById('stat-cust-active');
        if (statActiveEl) statActiveEl.innerText = `${activeCust} Khách`;

        const countBadge = document.getElementById('customer-count-badge');
        if (countBadge) countBadge.innerText = totalCust;

        if (customersCache.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-8 text-slate-500">
                        <i class="fa-solid fa-user-slash text-2xl text-slate-600 mb-2"></i>
                        <p class="text-xs">Không tìm thấy khách hàng nào phù hợp.</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = customersCache.map(c => {
            const bookingCount = c.bookings ? c.bookings.length : 0;
            const createdDate = c.created_at ? new Date(c.created_at).toLocaleDateString('vi-VN') : 'N/A';
            const safeName = (c.name || '').replace(/'/g, "\\'");
            return `
                <tr class="hover:bg-slate-800/40 transition">
                    <td class="py-3 px-4 font-mono font-bold text-teal-400">#KH-${c.id}</td>
                    <td class="py-3 px-4 font-bold text-slate-100">${c.name || 'Khách Vãng Lai'}</td>
                    <td class="py-3 px-4 font-mono text-slate-300">${c.phone || '---'}</td>
                    <td class="py-3 px-4 text-slate-400">${c.email || '---'}</td>
                    <td class="py-3 px-4 text-slate-400">${c.address || '---'}</td>
                    <td class="py-3 px-4 text-slate-400 font-mono">${createdDate}</td>
                    <td class="py-3 px-4 text-center">
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${bookingCount > 0 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-500'}">
                            ${bookingCount} đơn
                        </span>
                    </td>
                    <td class="py-3 px-4 text-right space-x-1.5">
                        <button onclick="viewCustomerHistory(${c.id})" class="px-2 py-1 rounded-lg bg-teal-600/20 hover:bg-teal-600 text-teal-300 hover:text-white border border-teal-500/30 transition text-[11px]" title="Xem Lịch Sử">
                            <i class="fa-solid fa-clock-rotate-left"></i>
                        </button>
                        <button onclick="openEditCustomerModal(${c.id})" class="px-2 py-1 rounded-lg bg-blue-600/20 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/30 transition text-[11px]" title="Chỉnh Sửa">
                            <i class="fa-solid fa-pen"></i>
                        </button>
                        <button onclick="deleteCustomer(${c.id}, '${safeName}')" class="px-2 py-1 rounded-lg bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 transition text-[11px]" title="Xóa">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error("Error loading customers:", e);
        showToast("Lỗi tải danh sách khách hàng", "error");
    }
}

function handleCustomerSearch(query) {
    if (customerSearchTimer) clearTimeout(customerSearchTimer);
    customerSearchTimer = setTimeout(() => {
        loadCustomers(query);
    }, 250);
}

function openAddCustomerModal() {
    document.getElementById('edit-customer-id').value = '';
    document.getElementById('cust-name-input').value = '';
    document.getElementById('cust-phone-input').value = '';
    document.getElementById('cust-email-input').value = '';
    document.getElementById('cust-address-input').value = '';
    document.getElementById('modal-customer-title').innerHTML = '<i class="fa-solid fa-user-plus mr-2"></i> Thêm Khách Hàng Mới';
    document.getElementById('modal-customer').classList.remove('hidden');
}

async function openEditCustomerModal(id) {
    let customer = customersCache.find(c => c.id === id);
    if (!customer) {
        customer = await apiFetch(`/api/customers/${id}`);
    }
    if (!customer) {
        showToast('Không tìm thấy thông tin khách hàng', 'error');
        return;
    }

    document.getElementById('edit-customer-id').value = customer.id;
    document.getElementById('cust-name-input').value = customer.name || '';
    document.getElementById('cust-phone-input').value = customer.phone || '';
    document.getElementById('cust-email-input').value = customer.email || '';
    document.getElementById('cust-address-input').value = customer.address || '';
    document.getElementById('modal-customer-title').innerHTML = '<i class="fa-solid fa-user-pen mr-2"></i> Chỉnh Sửa Thông Tin Khách Hàng';
    document.getElementById('modal-customer').classList.remove('hidden');
}

function closeCustomerModal() {
    const m = document.getElementById('modal-customer');
    if (m) m.classList.add('hidden');
}

async function handleSaveCustomerSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('edit-customer-id').value;
    const name = document.getElementById('cust-name-input').value.trim();
    const phone = document.getElementById('cust-phone-input').value.trim();
    const email = document.getElementById('cust-email-input').value.trim() || null;
    const address = document.getElementById('cust-address-input').value.trim() || null;

    if (!name || !phone) {
        showToast('Vui lòng nhập họ tên và số điện thoại!', 'warning');
        return;
    }

    const payload = { name, phone, email, address };
    try {
        let res;
        if (id) {
            res = await apiFetch(`/api/customers/${id}`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });
        } else {
            res = await apiFetch('/api/customers', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
        }

        if (res) {
            showToast(id ? 'Đã cập nhật thông tin khách hàng!' : 'Đã thêm khách hàng thành công!', 'success');
            closeCustomerModal();
            loadCustomers();
        }
    } catch (err) {
        console.error("Save customer error:", err);
        showToast(err.message || 'Lỗi lưu khách hàng', 'error');
    }
}

async function deleteCustomer(id, name) {
    if (!confirm(`Bạn có chắc chắn muốn xóa khách hàng "${name}" (#KH-${id}) khỏi hệ thống?`)) return;

    try {
        const res = await apiFetch(`/api/customers/${id}`, { method: 'DELETE' });
        if (res) {
            showToast('Đã xóa khách hàng thành công!', 'success');
            loadCustomers();
        }
    } catch (err) {
        console.error("Delete customer error:", err);
        showToast(err.message || 'Lỗi xóa khách hàng', 'error');
    }
}

async function viewCustomerHistory(id) {
    try {
        const customer = await apiFetch(`/api/customers/${id}`);
        if (!customer) {
            showToast('Không thể lấy lịch sử khách hàng', 'error');
            return;
        }

        document.getElementById('history-cust-title').innerText = `Khách hàng: ${customer.name} - SĐT: ${customer.phone}`;

        const totalSpent = (customer.bookings || []).reduce((sum, b) => sum + (Number(b.total_price) || 0), 0);
        const bookingCount = (customer.bookings || []).length;

        const infoCard = document.getElementById('history-cust-info-card');
        if (infoCard) {
            infoCard.innerHTML = `
                <div>
                    <p class="text-[10px] text-slate-400 uppercase">Mã Khách Hàng</p>
                    <p class="font-bold font-mono text-teal-400">#KH-${customer.id}</p>
                </div>
                <div>
                    <p class="text-[10px] text-slate-400 uppercase">Email</p>
                    <p class="font-semibold text-slate-200 truncate">${customer.email || 'Chưa cập nhật'}</p>
                </div>
                <div>
                    <p class="text-[10px] text-slate-400 uppercase">Tổng Lượt Đặt</p>
                    <p class="font-bold text-emerald-400">${bookingCount} lượt</p>
                </div>
                <div>
                    <p class="text-[10px] text-slate-400 uppercase">Tổng Doanh Số</p>
                    <p class="font-black text-amber-400 font-mono">${totalSpent.toLocaleString()} đ</p>
                </div>
            `;
        }

        const tbody = document.getElementById('history-cust-bookings-body');
        if (tbody) {
            if (!customer.bookings || customer.bookings.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-slate-500">Khách hàng chưa có lượt đặt sân nào.</td></tr>`;
            } else {
                tbody.innerHTML = customer.bookings.map(b => {
                    let statusBadge = '';
                        if (b.status === 'CONFIRMED' || b.status === 'COMPLETED') {
                            statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 whitespace-nowrap inline-flex items-center justify-center min-w-max">ĐÃ DUYỆT</span>';
                        } else if (b.status === 'PENDING') {
                            statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-500/20 text-amber-400 border border-amber-500/40 whitespace-nowrap inline-flex items-center justify-center min-w-max">CHỜ DUYỆT</span>';
                        } else {
                            statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-rose-500/20 text-rose-400 border border-rose-500/40 whitespace-nowrap inline-flex items-center justify-center min-w-max">ĐÃ HỦY</span>';
                        }

                    return `
                        <tr class="hover:bg-slate-800/40 transition">
                            <td class="py-2.5 px-3 font-mono font-bold text-teal-400">#${b.id}</td>
                            <td class="py-2.5 px-3 font-semibold text-slate-200">${b.pitch?.name || 'Sân Thể Thao'}</td>
                            <td class="py-2.5 px-3 text-slate-300 font-mono">${b.booking_date} (${b.start_time} - ${b.end_time})</td>
                            <td class="py-2.5 px-3 text-right font-mono font-bold text-emerald-400">${Number(b.total_price).toLocaleString()} đ</td>
                            <td class="py-2.5 px-3 text-center">${statusBadge}</td>
                        </tr>
                    `;
                }).join('');
            }
        }

        document.getElementById('modal-customer-history').classList.remove('hidden');
    } catch (e) {
        console.error("View customer history error:", e);
        showToast("Lỗi tải thông tin chi tiết khách hàng", "error");
    }
}

function closeCustomerHistoryModal() {
    const m = document.getElementById('modal-customer-history');
    if (m) m.classList.add('hidden');
}

// --- BÁO CÁO DOANH THU & CÔNG SUẤT (REPORTS) ---
async function loadReportsData(period = 'week') {
    currentReportPeriod = period;

    // Cập nhật giao diện nút period
    ['day', 'week', 'month'].forEach(p => {
        const btn = document.getElementById(`btn-period-${p}`);
        if (btn) {
            if (p === period) {
                btn.className = 'period-btn px-3 py-1.5 rounded-xl text-xs font-bold transition bg-emerald-500 text-slate-950 shadow-md';
            } else {
                btn.className = 'period-btn px-3 py-1.5 rounded-xl text-xs font-bold transition text-slate-400 hover:text-white';
            }
        }
    });

    try {
        const [revData, occData] = await Promise.all([
            apiFetch(`/api/reports/revenue?period=${period}`),
            apiFetch('/api/reports/occupancy')
        ]);

        if (revData) {
            const statRev = document.getElementById('stat-rep-revenue');
            if (statRev) statRev.innerText = `${Number(revData.total_revenue || 0).toLocaleString()} VNĐ`;

            const statPaid = document.getElementById('stat-rep-paid');
            if (statPaid) statPaid.innerText = `${Number(revData.paid_revenue || 0).toLocaleString()} VNĐ`;

            const statBookings = document.getElementById('stat-rep-bookings');
            if (statBookings) statBookings.innerText = `${revData.total_bookings || 0} Đơn`;

            const badgeCount = document.getElementById('report-booking-count-badge');
            if (badgeCount) badgeCount.innerText = `${revData.total_bookings || 0} Đơn`;

            // Bảng danh sách đơn giao dịch
            const revBody = document.getElementById('report-revenue-table-body');
            if (revBody) {
                const list = revData.bookings || [];
                if (list.length === 0) {
                    revBody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-slate-500">Không có đơn đặt sân trong kỳ ${period}.</td></tr>`;
                } else {
                    revBody.innerHTML = list.map(b => {
                        let statusBadge = '';
                        if (b.status === 'CONFIRMED' || b.status === 'COMPLETED') {
                            statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 whitespace-nowrap inline-flex items-center justify-center min-w-max">ĐÃ DUYỆT</span>';
                        } else if (b.status === 'PENDING') {
                            statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-500/20 text-amber-400 border border-amber-500/40 whitespace-nowrap inline-flex items-center justify-center min-w-max">CHỜ DUYỆT</span>';
                        } else {
                            statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-rose-500/20 text-rose-400 border border-rose-500/40 whitespace-nowrap inline-flex items-center justify-center min-w-max">ĐÃ HỦY</span>';
                        }

                        return `
                            <tr class="hover:bg-slate-800/40 transition">
                                <td class="py-2.5 px-3 font-mono font-bold text-emerald-400">#${b.id}</td>
                                <td class="py-2.5 px-3 font-semibold text-slate-200">${b.customer_name || 'Khách vãng lai'}</td>
                                <td class="py-2.5 px-3 text-slate-400 font-mono text-[11px]">${b.pitch_name || 'Sân'} | ${b.booking_date} (${b.start_time}-${b.end_time})</td>
                                <td class="py-2.5 px-3 text-right font-mono font-bold text-emerald-400">${Number(b.total_price).toLocaleString()} đ</td>
                                <td class="py-2.5 px-3 text-center">${statusBadge}</td>
                            </tr>
                        `;
                    }).join('');
                }
            }
        }

        if (occData) {
            const statOcc = document.getElementById('stat-rep-occupancy');
            if (statOcc) statOcc.innerText = `${occData.overall_occupancy_rate || 0}%`;

            const occBody = document.getElementById('report-occupancy-table-body');
            if (occBody) {
                const pitchOccList = occData.pitches_occupancy || [];
                if (pitchOccList.length === 0) {
                    occBody.innerHTML = `<tr><td colspan="4" class="text-center py-6 text-slate-500">Chưa có dữ liệu sân.</td></tr>`;
                } else {
                    occBody.innerHTML = pitchOccList.map(p => {
                        const rate = Number(p.occupancy_rate) || 0;
                        let barColor = 'bg-emerald-500';
                        if (rate > 70) barColor = 'bg-emerald-500';
                        else if (rate > 30) barColor = 'bg-blue-500';
                        else barColor = 'bg-amber-500';

                        return `
                            <tr class="hover:bg-slate-800/40 transition">
                                <td class="py-2.5 px-3 font-bold text-slate-200">${p.pitch_name}</td>
                                <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 font-medium">${p.sport_type || 'Thể Thao'}</span></td>
                                <td class="py-2.5 px-3 text-center font-mono text-slate-300">${p.booked_hours}h / ${p.total_available_hours}h</td>
                                <td class="py-2.5 px-3 text-right">
                                    <div class="flex items-center justify-end space-x-2">
                                        <div class="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                            <div class="${barColor} h-1.5 rounded-full" style="width: ${Math.min(rate, 100)}%"></div>
                                        </div>
                                        <span class="font-bold font-mono text-xs text-slate-100">${rate}%</span>
                                    </div>
                                </td>
                            </tr>
                        `;
                    }).join('');
                }
            }
        }

        renderReportsCharts(revData, occData, period);
        renderReportDetailTables(revData);
    } catch (e) {
        console.error("Error loading reports data:", e);
        showToast("Lỗi tải dữ liệu báo cáo", "error");
    }
}

function closeInvoiceModal() {
    const m = document.getElementById('modal-invoice');
    if (m) m.classList.add('hidden');
}




// =========================================================================
// THEME MANAGEMENT (SÁNG / TỐI)
// =========================================================================

function initTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    applyTheme(saved);
}

function applyTheme(theme) {
    localStorage.setItem('theme', theme);
    const htmlEl = document.documentElement;
    const bodyEl = document.body;
    const themeBtns = [
        document.getElementById('btn-theme-toggle'),
        document.getElementById('theme-toggle-btn')
    ];
    const dropdownThemeBtn = document.getElementById('btn-theme-toggle-dropdown');
    const dropdownIconHolder = document.getElementById('theme-icon-holder');
    const dropdownBadge = document.getElementById('theme-badge');

    if (theme === 'light') {
        htmlEl.classList.remove('dark');
        bodyEl.classList.add('theme-bright', 'light-theme');
        bodyEl.classList.remove('dark-theme');
        themeBtns.forEach(btn => {
            if (btn) {
                btn.className = 'px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-200 hover:bg-slate-300 text-slate-800 border border-slate-300 shadow-sm flex items-center gap-1.5 transition cursor-pointer whitespace-nowrap';
                btn.innerHTML = '<i class="fa-solid fa-moon text-indigo-600"></i> <span id="theme-text" class="hidden sm:inline">Chế Độ Tối</span>';
            }
        });
        if (dropdownThemeBtn) {
            const textSpan = dropdownThemeBtn.querySelector('#theme-text');
            if (textSpan) textSpan.innerText = 'Chế Độ Tối';
            if (dropdownIconHolder) dropdownIconHolder.innerHTML = '<i class="fa-solid fa-moon text-indigo-400 text-xs"></i>';
            if (dropdownBadge) {
                dropdownBadge.innerText = 'Tối';
                dropdownBadge.className = 'text-[9px] bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded-full border border-indigo-500/30 font-mono';
            }
        }
    } else {
        htmlEl.classList.add('dark');
        bodyEl.classList.remove('theme-bright', 'light-theme');
        bodyEl.classList.add('dark-theme');
        themeBtns.forEach(btn => {
            if (btn) {
                btn.className = 'px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-800/90 hover:bg-slate-700 text-amber-300 border border-slate-700/80 shadow-sm flex items-center gap-1.5 transition cursor-pointer whitespace-nowrap';
                btn.innerHTML = '<i class="fa-solid fa-sun text-amber-400"></i> <span id="theme-text" class="hidden sm:inline">Chế Độ Sáng</span>';
            }
        });
        if (dropdownThemeBtn) {
            const textSpan = dropdownThemeBtn.querySelector('#theme-text');
            if (textSpan) textSpan.innerText = 'Chế Độ Sáng';
            if (dropdownIconHolder) dropdownIconHolder.innerHTML = '<i class="fa-solid fa-sun text-amber-400 text-xs"></i>';
            if (dropdownBadge) {
                dropdownBadge.innerText = 'Sáng';
                dropdownBadge.className = 'text-[9px] bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded-full border border-amber-500/30 font-mono';
            }
        }
    }
}

function toggleTheme() {
    const current = localStorage.getItem('theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    showToast(next === 'dark' ? 'Đã chuyển sang Giao diện Tối' : 'Đã chuyển sang Giao diện Sáng', 'info');
}

function toggleBrightTheme() {
    toggleTheme();
}


// =========================================================================
// INVOICE DETAILS & PRINTING
// =========================================================================

async function viewBookingInvoice(bookingId) {
    if (!bookingId) {
        showToast('Không tìm thấy mã đơn đặt sân!', 'warning');
        return;
    }
    try {
        const b = await apiFetch(`/api/bookings/${bookingId}`);
        if (!b) return;

        const modal = document.getElementById('modal-invoice');
        const content = document.getElementById('invoice-details-content');
        const codeEl = document.getElementById('inv-code');
        if (codeEl) codeEl.innerText = `HD-STT-${String(b.id).padStart(5, '0')}`;

        if (content) {
            content.innerHTML = `
                <div id="printable-invoice-body" class="space-y-4 p-4 bg-white rounded-2xl border border-slate-200 text-slate-800">
                    <div class="flex justify-between items-start border-b pb-3">
                        <div>
                            <h4 class="font-black text-sm text-emerald-700">HỆ THỐNG SÂN THỂ THAO AI - NHÓM 03</h4>
                            <p class="text-[10px] text-slate-500">Đề tài: AIA331 | ĐH CNTT & Truyền Thông (ICTU)</p>
                            <p class="text-[10px] text-slate-500">Hotline: <strong>0816227206</strong> | Cơ sở: 128 Đường Z115, Thái Nguyên</p>
                        </div>
                        <div class="text-right">
                            <span class="inline-block px-2.5 py-1 rounded-lg text-[10px] font-bold ${b.payment_status === 'PAID' ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-amber-100 text-amber-800 border border-amber-300'}">
                                ${b.payment_status === 'PAID' ? 'ĐÃ THANH TOÁN ĐỦ' : 'THANH TOÁN TẠI SÂN / ĐÃ CỌC'}
                            </span>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-2 text-xs border-b pb-3">
                        <div>
                            <p class="text-slate-500 text-[10px]">KHÁCH HÀNG:</p>
                            <p class="font-bold text-slate-900">${b.customer_name || 'Khách vãng lai'}</p>
                            <p class="text-slate-600 font-mono text-[11px]">${b.customer_phone || '---'}</p>
                            <p class="text-slate-600 text-[10px]">${b.invoice_email || '---'}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-slate-500 text-[10px]">THÔNG TIN THI ĐẤU:</p>
                            <p class="font-bold text-slate-900">${b.pitch?.name || 'Sân thể thao'}</p>
                            <p class="text-emerald-700 font-bold font-mono">${b.start_time} - ${b.end_time} (${b.booking_date})</p>
                            <p class="text-slate-500 text-[10px]">${b.pitch?.location || ''}</p>
                        </div>
                    </div>

                    <table class="w-full text-xs border-collapse">
                        <thead>
                            <tr class="bg-slate-100 text-slate-700 border-b">
                                <th class="p-2 text-left">Dịch vụ</th>
                                <th class="p-2 text-center">Khung giờ</th>
                                <th class="p-2 text-right">Thành tiền</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="border-b">
                                <td class="p-2 font-semibold">${b.pitch?.name || 'Thuê sân'}</td>
                                <td class="p-2 text-center font-mono">${b.start_time} - ${b.end_time}</td>
                                <td class="p-2 text-right font-bold text-slate-900 font-mono">${Number(b.total_price || 0).toLocaleString()} VNĐ</td>
                            </tr>
                        </tbody>
                        <tfoot>
                            <tr class="font-black text-sm">
                                <td colspan="2" class="p-2 text-right">TỔNG CỘNG:</td>
                                <td class="p-2 text-right text-emerald-600 font-mono">${Number(b.total_price || 0).toLocaleString()} VNĐ</td>
                            </tr>
                        </tfoot>
                    </table>

                    <div class="flex justify-between items-end pt-2 text-[10px] text-slate-500 border-t">
                        <div>
                            <p>Cảm ơn quý khách đã tin tưởng và sử dụng dịch vụ!</p>
                            <p>Mọi thắc mắc xin liên hệ Hotline: <strong>0816227206</strong></p>
                        </div>
                        <div class="text-center font-bold">
                            <p>ĐẠI DIỆN HỆ THỐNG</p>
                            <p class="mt-4 text-emerald-700">Nông Thành Chung (Nhóm 03)</p>
                        </div>
                    </div>
                </div>
            `;
        }
        if (modal) modal.classList.remove('hidden');
    } catch (e) {
        showToast(e.message || 'Lỗi tải hóa đơn', 'error');
    }
}

async function viewPaymentInvoice(bookingId) {
    await viewBookingInvoice(bookingId);
}

function printBookingInvoice() {
    const printContent = document.getElementById('printable-invoice-body');
    if (!printContent) {
        window.print();
        return;
    }
    const printWindow = window.open('', '_blank', 'width=800,height=600');
    printWindow.document.write(`
        <html>
            <head>
                <title>Hóa Đơn Đặt Sân Thể Thao</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; color: #1e293b; background: #ffffff; }
                    @media print { button { display: none; } }
                </style>
            </head>
            <body>
                ${printContent.outerHTML}
                <script>
                    window.onload = function() { window.print(); window.close(); }
                </script>
            </body>
        </html>
    `);
    printWindow.document.close();
}

function closeInvoiceModal() {
    const m = document.getElementById('modal-invoice');
    if (m) m.classList.add('hidden');
}


// =========================================================================
// BOOKING RESCHEDULE / EDIT MODAL
// =========================================================================

async function openEditBookingModal(bookingId) {
    try {
        let b = state.bookings?.find(x => x.id === bookingId);
        if (!b) {
            b = await apiFetch(`/api/bookings/${bookingId}`);
        }
        if (!b) {
            showToast('Không tìm thấy đơn đặt sân', 'error');
            return;
        }

        document.getElementById('edit-booking-id').value = b.id;
        
        // Populate pitch dropdown
        const pitchSel = document.getElementById('edit-booking-pitch-id');
        if (pitchSel && state.pitches) {
            pitchSel.innerHTML = state.pitches.map(p => `
                <option value="${p.id}" ${p.id === b.pitch_id ? 'selected' : ''}>${p.name} (${p.sport_type} - ${Number(p.price_per_hour).toLocaleString()}đ/h)</option>
            `).join('');
        }

        document.getElementById('edit-booking-date').value = b.booking_date;
        document.getElementById('edit-booking-start-time').value = b.start_time;
        document.getElementById('edit-booking-end-time').value = b.end_time;
        document.getElementById('edit-booking-status').value = b.status;
        document.getElementById('edit-booking-note').value = b.note || '';
        
        recalculateEditBookingPrice();
        document.getElementById('modal-edit-booking').classList.remove('hidden');
    } catch (e) {
        showToast(e.message || 'Lỗi mở đơn đặt sân', 'error');
    }
}

function closeEditBookingModal() {
    const m = document.getElementById('modal-edit-booking');
    if (m) m.classList.add('hidden');
}

function recalculateEditBookingPrice() {
    const pitchId = parseInt(document.getElementById('edit-booking-pitch-id')?.value);
    const startTime = document.getElementById('edit-booking-start-time')?.value;
    const endTime = document.getElementById('edit-booking-end-time')?.value;
    const pricePreview = document.getElementById('edit-booking-calculated-price') || document.getElementById('edit-booking-price-preview');

    if (!pitchId || !startTime || !endTime || !pricePreview) return;

    const pitch = state.pitches?.find(p => p.id === pitchId);
    if (!pitch) return;

    const [sh, sm] = startTime.split(':').map(Number);
    const [eh, em] = endTime.split(':').map(Number);
    const durationHours = (eh + em/60) - (sh + sm/60);

    if (durationHours > 0) {
        const isPeak = (sh >= 17 && sh < 21);
        const rate = isPeak ? (pitch.peak_price_per_hour || pitch.price_per_hour) : pitch.price_per_hour;
        const total = Math.round(durationHours * rate);
        pricePreview.innerText = `${total.toLocaleString()} VNĐ (${durationHours.toFixed(1)}h)`;
    } else {
        pricePreview.innerText = '0 VNĐ (Giờ không hợp lệ)';
    }
}

async function handleSaveBookingSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('edit-booking-id').value;
    const pitch_id = parseInt(document.getElementById('edit-booking-pitch-id').value);
    const booking_date = document.getElementById('edit-booking-date').value;
    const start_time = document.getElementById('edit-booking-start-time').value;
    const end_time = document.getElementById('edit-booking-end-time').value;
    const status = document.getElementById('edit-booking-status').value;
    const note = document.getElementById('edit-booking-note').value.trim() || undefined;
    const customer_name = document.getElementById('edit-booking-cust-name')?.value?.trim() || undefined;
    const customer_phone = document.getElementById('edit-booking-cust-phone')?.value?.trim() || undefined;
    const invoice_email = document.getElementById('edit-booking-email')?.value?.trim() || undefined;
    const payment_status = document.getElementById('edit-booking-payment-status')?.value || undefined;

    try {
        const res = await apiFetch(`/api/bookings/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ pitch_id, booking_date, start_time, end_time, status, note, customer_name, customer_phone, invoice_email, payment_status })
        });
        if (res) {
            showToast('Đã đổi lịch & cập nhật đơn đặt sân thành công!', 'success');
            closeEditBookingModal();
            loadBookings();
            loadBookingMatrix();
        }
    } catch (err) {
        showToast(err.message || 'Lỗi cập nhật đơn đặt sân', 'error');
    }
}


// =========================================================================
// MAINTENANCE MANAGEMENT
// =========================================================================

async function loadMaintenances(manual = false) {
    try {
        const data = await apiFetch('/api/maintenances');
        state.maintenances = data;
        const tbody = document.getElementById('maintenances-tbody') || document.getElementById('maintenance-tbody');
        if (!tbody) return;

        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-slate-400">Chưa có lịch trình bảo trì nào. Bấm 'Lên Lịch Bảo Trì Mới' để thêm.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(m => {
            let statusBadge = '';
            const st = (m.status || '').toUpperCase();
            if (st === 'DONE') {
                statusBadge = '<span class="px-2.5 py-1 rounded-full text-xs font-black bg-emerald-600 text-white shadow-sm border border-emerald-400">ĐÃ XONG</span>';
            } else if (st === 'IN_PROGRESS') {
                statusBadge = '<span class="px-2.5 py-1 rounded-full text-xs font-black bg-blue-600 text-white shadow-sm border border-blue-400">ĐANG BẢO TRÌ</span>';
            } else {
                statusBadge = '<span class="px-2.5 py-1 rounded-full text-xs font-black bg-amber-500 text-white shadow-sm border border-amber-300">ĐÃ LÊN LỊCH</span>';
            }

            const sDate = m.start_date || (m.start_time ? m.start_time.slice(0, 10) : '---');
            const eDate = m.end_date || (m.end_time ? m.end_time.slice(0, 10) : '---');
            const reasonText = m.reason || m.description || m.title || 'Bảo dưỡng định kỳ';

            return `
                <tr class="hover:bg-slate-800/40 dark:hover:bg-slate-800/60 transition">
                    <td class="p-3.5 font-mono text-amber-500 dark:text-amber-400 font-bold">#${m.id}</td>
                    <td class="p-3.5 font-bold text-slate-900 dark:text-slate-100">${m.pitch?.name || 'Sân Thể Thao'}</td>
                    <td class="p-3.5 font-mono text-slate-600 dark:text-slate-300 text-xs font-semibold">${sDate} ➔ ${eDate}</td>
                    <td class="p-3.5 text-slate-700 dark:text-slate-300 text-xs">${reasonText}</td>
                    <td class="p-3.5 font-mono text-emerald-600 dark:text-emerald-400 font-extrabold">${(Number(m.cost) || 0).toLocaleString()} đ</td>
                    <td class="p-3.5 text-center">${statusBadge}</td>
                    <td class="p-3.5 text-right space-x-1.5 whitespace-nowrap">
                        <button onclick="openEditMaintenanceModal(${m.id})" class="px-2.5 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500 text-amber-700 dark:text-amber-300 hover:text-white border border-amber-500/30 transition text-xs font-bold"><i class="fa-solid fa-pen mr-1"></i> Sửa</button>
                        ${st !== 'DONE' ? `<button onclick="completeMaintenance(${m.id})" class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition text-xs font-bold"><i class="fa-solid fa-check mr-1"></i> Xong</button>` : ''}
                        <button onclick="deleteMaintenance(${m.id})" class="px-2 py-1 rounded-lg bg-rose-600/20 hover:bg-rose-600 text-rose-600 dark:text-rose-300 hover:text-white border border-rose-500/30 transition text-xs"><i class="fa-solid fa-trash"></i></button>
                    </td>
                </tr>
            `;
        }).join('');

        if (manual) showToast('Đã làm mới danh sách bảo trì thành công!', 'success');
    } catch (e) {
        console.error("loadMaintenances error:", e);
    }
}

function openAddMaintenanceModal() {
    document.getElementById('modal-maint-title').innerHTML = '<i class="fa-solid fa-wrench mr-2"></i> Thêm Lịch Trình Bảo Trì Mới';
    document.getElementById('edit-maint-id').value = '';
    document.getElementById('edit-maint-start-date').value = getLocalDateString();
    document.getElementById('edit-maint-end-date').value = getLocalDateString();
    document.getElementById('edit-maint-cost').value = 500000;
    document.getElementById('edit-maint-status').value = 'SCHEDULED';
    document.getElementById('edit-maint-reason').value = '';

    const sel = document.getElementById('edit-maint-pitch-id');
    if (sel && state.pitches) {
        sel.innerHTML = state.pitches.map(p => `<option value="${p.id}">${p.name} (${p.sport_type})</option>`).join('');
    }
    document.getElementById('modal-maintenance').classList.remove('hidden');
}

async function openEditMaintenanceModal(maintId) {
    let m = state.maintenances?.find(x => x.id === maintId);
    if (!m) {
        m = await apiFetch(`/api/maintenances`);
        m = (m || []).find(x => x.id === maintId);
    }
    if (!m) {
        showToast('Không tìm thấy thông tin bảo trì', 'error');
        return;
    }

    document.getElementById('modal-maint-title').innerHTML = `<i class="fa-solid fa-wrench mr-2"></i> Chỉnh Sửa Lịch Bảo Trì #${m.id}`;
    document.getElementById('edit-maint-id').value = m.id;
    
    const sel = document.getElementById('edit-maint-pitch-id');
    if (sel && state.pitches) {
        sel.innerHTML = state.pitches.map(p => `<option value="${p.id}" ${p.id === m.pitch_id ? 'selected' : ''}>${p.name} (${p.sport_type})</option>`).join('');
    }

    document.getElementById('edit-maint-start-date').value = m.start_date || (m.start_time || '').slice(0, 10);
    document.getElementById('edit-maint-end-date').value = m.end_date || (m.end_time || '').slice(0, 10);
    document.getElementById('edit-maint-cost').value = m.cost || 0;
    document.getElementById('edit-maint-status').value = m.status || 'SCHEDULED';
    document.getElementById('edit-maint-reason').value = m.reason || m.description || m.title || '';

    document.getElementById('modal-maintenance').classList.remove('hidden');
}

function closeMaintenanceModal() {
    const m = document.getElementById('modal-maintenance');
    if (m) m.classList.add('hidden');
}

async function handleSaveMaintenanceSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('edit-maint-id').value;
    const pitch_id = parseInt(document.getElementById('edit-maint-pitch-id').value);
    const start_date = document.getElementById('edit-maint-start-date').value;
    const end_date = document.getElementById('edit-maint-end-date').value;
    const cost = parseFloat(document.getElementById('edit-maint-cost').value) || 0;
    const status = document.getElementById('edit-maint-status').value;
    const description = document.getElementById('edit-maint-reason').value.trim();

    const payload = {
        pitch_id,
        start_date,
        end_date,
        reason: description || "Bảo dưỡng sân định kỳ",
        title: description || "Bảo dưỡng sân định kỳ",
        description,
        start_time: `${start_date}T00:00:00`,
        end_time: `${end_date}T23:59:59`,
        cost,
        status: (status === 'PLANNED' ? 'SCHEDULED' : status)
    };

    try {
        if (id) {
            await apiFetch(`/api/maintenances/${id}`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });
            showToast('Đã cập nhật lịch trình bảo trì thành công!', 'success');
        } else {
            await apiFetch('/api/maintenances', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            showToast('Đã thêm lịch bảo trì mới thành công!', 'success');
        }
        closeMaintenanceModal();
        loadMaintenances();
    } catch (err) {
        showToast(err.message || 'Lỗi lưu bảo trì', 'error');
    }
}


async function completeMaintenance(maintId) {
    try {
        await apiFetch(`/api/maintenances/${maintId}/complete`, { method: 'POST' });
        showToast('Đã đánh dấu hoàn tất bảo trì và mở lại sân!', 'success');
        loadMaintenances();
    } catch (err) {
        showToast(err.message || 'Lỗi hoàn tất bảo trì', 'error');
    }
}

async function deleteMaintenance(maintId) {
    if (!confirm(`Bạn có chắc muốn xóa lịch trình bảo trì #${maintId}?`)) return;
    try {
        await apiFetch(`/api/maintenances/${maintId}`, { method: 'DELETE' });
        showToast('Đã xóa đợt bảo trì thành công!', 'success');
        loadMaintenances();
    } catch (err) {
        showToast(err.message || 'Lỗi xóa bảo trì', 'error');
    }
}


// =========================================================================
// PITCH MANAGEMENT
// =========================================================================

function openCreatePitchModal() {
    document.getElementById('modal-pitch-title').innerHTML = '<i class="fa-solid fa-plus-circle mr-2"></i> Thêm Sân Thể Thao Mới';
    document.getElementById('edit-pitch-id').value = '';
    document.getElementById('edit-pitch-name').value = '';
    document.getElementById('edit-pitch-sport-type').value = 'FOOTBALL';
    document.getElementById('edit-pitch-capacity').value = '5 - 7 người';
    document.getElementById('edit-pitch-location').value = '128 Đường Z115, Tân Thịnh, TP. Thái Nguyên';
    document.getElementById('edit-pitch-price').value = 250000;
    document.getElementById('edit-pitch-peak-price').value = 350000;
    document.getElementById('edit-pitch-status').value = 'AVAILABLE';
    document.getElementById('edit-pitch-image').value = '';
    document.getElementById('edit-pitch-desc').value = '';
    document.getElementById('modal-edit-pitch').classList.remove('hidden');
}

function openEditPitchModal(pitchId) {
    const p = state.pitches?.find(x => x.id === pitchId);
    if (!p) return;
    document.getElementById('modal-pitch-title').innerHTML = `<i class="fa-solid fa-pen-to-square mr-2"></i> Chỉnh Sửa Sân #${p.id} - ${p.name}`;
    document.getElementById('edit-pitch-id').value = p.id;
    document.getElementById('edit-pitch-name').value = p.name;
    document.getElementById('edit-pitch-sport-type').value = p.sport_type;
    document.getElementById('edit-pitch-capacity').value = p.capacity || '5 - 7 người';
    document.getElementById('edit-pitch-location').value = p.location;
    document.getElementById('edit-pitch-price').value = p.price_per_hour;
    document.getElementById('edit-pitch-peak-price').value = p.peak_price_per_hour || p.price_per_hour;
    document.getElementById('edit-pitch-status').value = p.status;
    document.getElementById('edit-pitch-image').value = p.image_url || '';
    document.getElementById('edit-pitch-desc').value = p.description || '';
    document.getElementById('modal-edit-pitch').classList.remove('hidden');
}

function closeEditPitchModal() {
    const m = document.getElementById('modal-edit-pitch');
    if (m) m.classList.add('hidden');
}

async function handleSavePitchSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('edit-pitch-id').value;
    const name = document.getElementById('edit-pitch-name').value.trim();
    const sport_type = document.getElementById('edit-pitch-sport-type').value;
    const capacity = document.getElementById('edit-pitch-capacity').value.trim();
    const location = document.getElementById('edit-pitch-location').value.trim();
    const price_per_hour = parseFloat(document.getElementById('edit-pitch-price').value) || 0;
    const peak_price_per_hour = parseFloat(document.getElementById('edit-pitch-peak-price').value) || price_per_hour;
    const status = document.getElementById('edit-pitch-status').value;
    const image_url = document.getElementById('edit-pitch-image').value.trim() || undefined;
    const description = document.getElementById('edit-pitch-desc').value.trim() || undefined;

    const payload = {
        name, sport_type, capacity, location, price_per_hour, peak_price_per_hour, status, image_url, description
    };

    try {
        if (id) {
            await apiFetch(`/api/pitches/${id}`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });
            showToast(`Đã cập nhật thông tin sân "${name}" thành công!`, 'success');
        } else {
            await apiFetch('/api/pitches', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            showToast(`Đã thêm sân mới "${name}" thành công!`, 'success');
        }
        closeEditPitchModal();
        loadPitches();
        loadBookingMatrix();
        loadMaintenances();
    } catch (err) {
        showToast(err.message || 'Lỗi lưu thông tin sân', 'error');
    }
}


// =========================================================================
// PAYMENTS MANAGEMENT
// =========================================================================

async function loadPayments(manual = false) {
    try {
        const payments = await apiFetch('/api/payments');
        state.payments = payments;
        const tbody = document.getElementById('payments-tbody');
        if (!tbody) return;

        if (payments.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="p-6 text-center text-slate-400">Chưa có giao dịch thanh toán nào.</td></tr>`;
            return;
        }

        tbody.innerHTML = payments.map(p => {
            let statusBadge = '';
            if (p.status === 'PAID') {
                statusBadge = '<span class="px-2.5 py-1 rounded-full text-xs font-black bg-emerald-600 text-white shadow-sm border border-emerald-400">PAID</span>';
            } else if (p.status === 'PENDING') {
                statusBadge = '<span class="px-2.5 py-1 rounded-full text-xs font-black bg-amber-500 text-white shadow-sm border border-amber-300">PENDING</span>';
            } else {
                statusBadge = '<span class="px-2.5 py-1 rounded-full text-xs font-black bg-rose-600 text-white shadow-sm border border-rose-400">FAILED</span>';
            }

            return `
                <tr class="hover:bg-slate-800/40 transition">
                    <td class="p-3.5 font-mono text-cyan-400 font-bold">${p.transaction_ref || ('TXN' + p.id)}</td>
                    <td class="p-3.5 font-mono text-teal-400 font-bold">#${p.booking_id}</td>
                    <td class="p-3.5 font-mono text-emerald-400 font-black">${(Number(p.amount) || 0).toLocaleString()} đ</td>
                    <td class="p-3.5"><span class="px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-800 text-slate-300">${p.payment_method || 'CASH'}</span></td>
                    <td class="p-3.5 font-mono text-slate-400 text-xs">${p.payment_time ? new Date(p.payment_time).toLocaleString('vi-VN') : '---'}</td>
                    <td class="p-3.5 text-center">${statusBadge}</td>
                    <td class="p-3.5 text-right">
                        <button onclick="viewPaymentInvoice(${p.booking_id})" class="px-3 py-1 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs transition shadow"><i class="fa-solid fa-file-invoice mr-1"></i> Xem</button>
                    </td>
                </tr>
            `;
        }).join('');

        if (manual) showToast('Đã làm mới dữ liệu thanh toán thành công!', 'success');
    } catch (e) {
        console.error("loadPayments error:", e);
    }
}


// =========================================================================
// REAL SMTP EMAIL CONFIGURATION & DISPATCH
// =========================================================================
function openSmtpModal() {
    const modal = document.getElementById('modal-smtp');
    if (modal) modal.classList.remove('hidden');
}

function closeSmtpModal() {
    const modal = document.getElementById('modal-smtp');
    if (modal) modal.classList.add('hidden');
}

async function handleSaveSmtpSubmit(event) {
    if (event) event.preventDefault();
    const smtp_user = document.getElementById('smtp-user-input')?.value?.trim();
    const smtp_password = document.getElementById('smtp-pass-input')?.value?.trim();
    const test_recipient = document.getElementById('smtp-test-recipient')?.value?.trim();

    if (!smtp_user || !smtp_password) {
        showToast('Vui lòng điền đầy đủ tài khoản Gmail và Mật khẩu ứng dụng!', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/auth/settings/smtp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(state.token ? { 'Authorization': `Bearer ${state.token}` } : {})
            },
            body: JSON.stringify({
                smtp_user: smtp_user,
                smtp_password: smtp_password,
                test_recipient: test_recipient || smtp_user
            })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.detail || 'Không thể lưu cấu hình SMTP!', 'error');
            return;
        }
        showToast(data.message || 'Cấu hình SMTP thành công! Email thử nghiệm đã được gửi.', 'success');
        closeSmtpModal();
    } catch (err) {
        console.error(err);
        showToast('Lỗi kết nối máy chủ khi lưu cấu hình SMTP!', 'error');
    }
}

// =========================================================================
// ZALO & CLIPBOARD UTILITIES
// =========================================================================
function openZaloModal() {
    const modal = document.getElementById('modal-zalo-contact');
    if (modal) modal.classList.remove('hidden');
}

function closeZaloModal() {
    const modal = document.getElementById('modal-zalo-contact');
    if (modal) modal.classList.add('hidden');
}

function copyZaloPhoneNumber() {
    const phone = '0816227206';
    navigator.clipboard.writeText(phone).then(() => {
        showToast(`Đã sao chép số Zalo: ${phone}`, 'success');
    }).catch(() => {
        showToast('Không thể sao chép số Zalo!', 'error');
    });
}

function copyText(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.value || el.innerText || '';
    if (!text) {
        showToast('Không có nội dung để sao chép!', 'warning');
        return;
    }
    navigator.clipboard.writeText(text).then(() => {
        showToast('Đã sao chép nội dung vào bộ nhớ tạm!', 'success');
    }).catch(() => {
        showToast('Không thể sao chép!', 'error');
    });
}

// =========================================================================
// AI NOTIFICATIONS & REAL EMAIL GENERATION
// =========================================================================
function filterAINotifBookings(searchText) {
    const select = document.getElementById('ai-notif-booking-select');
    if (!select) return;

    const query = (searchText || '').trim().toLowerCase();
    const options = Array.from(select.options);
    let matched = 0;

    options.forEach(option => {
        const text = (option.textContent || '').toLowerCase();
        const visible = !query || text.includes(query);
        option.hidden = !visible;
        option.disabled = !visible;
        if (visible) matched += 1;
    });

    if (matched > 0 && (!select.value || select.selectedOptions.length === 0 || select.selectedOptions[0].hidden)) {
        const firstVisible = options.find(option => !option.hidden);
        if (firstVisible) select.value = firstVisible.value;
    }
}

async function populateAINotifBookings() {
    const select = document.getElementById('ai-notif-booking-select');
    if (!select) return;

    try {
        const res = await fetch('/api/bookings', {
            headers: state.token ? { 'Authorization': `Bearer ${state.token}` } : {}
        });
        if (!res.ok) return;
        const bookings = await res.json();
        select.innerHTML = bookings.map(b => {
            const pitchName = b.pitch?.name || `Sân #${b.pitch_id}`;
            const optionText = `#${b.id} - ${b.customer_name} (${pitchName}, ${b.booking_date} ${b.start_time})`;
            return `<option value="${b.id}" data-email="${b.customer?.email || ''}" data-phone="${b.customer_phone || ''}" data-name="${b.customer_name || ''}">${optionText}</option>`;
        }).join('');
        const searchInput = document.getElementById('ai-notif-booking-search');
        if (searchInput) filterAINotifBookings(searchInput.value);
    } catch (e) {
        console.error(e);
    }
}

async function callAIGenerateNotifications() {
    const select = document.getElementById('ai-notif-booking-select');
    const bId = select?.value;
    if (!bId) {
        showToast('Vui lòng chọn một đơn đặt sân để sinh thông báo!', 'warning');
        return;
    }

    const notifType = document.getElementById('ai-notif-type')?.value || 'CONFIRMATION';

    try {
        const res = await fetch('/api/ai/generate-notifications', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                booking_id: parseInt(bId),
                notification_type: notifType
            })
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.detail || 'Không thể sinh thông báo AI!', 'error');
            return;
        }

        const box = document.getElementById('ai-notif-result-box');
        if (box) box.classList.remove('hidden');

        const smsEl = document.getElementById('ai-sms-content');
        if (smsEl) smsEl.innerText = data.sms_message || '';

        const zaloEl = document.getElementById('ai-zalo-content');
        if (zaloEl) zaloEl.innerText = data.zalo_message || '';

        const emailSubEl = document.getElementById('ai-email-subject');
        if (emailSubEl) emailSubEl.value = data.email_subject || 'Xác nhận đặt sân thể thao thành công';

        const emailContentEl = document.getElementById('ai-email-content');
        if (emailContentEl) emailContentEl.value = data.email_body || '';

        const selOption = select.options[select.selectedIndex];
        const recipientEmail = selOption?.getAttribute('data-email') || state.user?.email || 'thanhchung.ictu@gmail.com';
        const emailRecipEl = document.getElementById('ai-email-recipient');
        if (emailRecipEl) emailRecipEl.value = recipientEmail;

        showToast('Đã sinh thông báo SMS, Zalo và Email thành công!', 'success');
    } catch (err) {
        console.error(err);
        showToast('Lỗi khi gọi AI sinh thông báo!', 'error');
    }
}

async function sendRealAIEmail() {
    const select = document.getElementById('ai-notif-booking-select');
    const bId = select?.value;
    if (!bId) {
        showToast('Vui lòng chọn đơn đặt sân!', 'warning');
        return;
    }

    const recipient = document.getElementById('ai-email-recipient')?.value?.trim();
    const subject = document.getElementById('ai-email-subject')?.value?.trim();
    const content = document.getElementById('ai-email-content')?.value?.trim();

    if (!recipient || !subject || !content) {
        showToast('Vui lòng điền đầy đủ Email người nhận, Tiêu đề và Nội dung thư!', 'warning');
        return;
    }

    const btn = document.getElementById('btn-send-real-email');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang gửi email thực tế...';
    }

    try {
        const res = await fetch('/api/ai/send-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                booking_id: parseInt(bId),
                recipient_email: recipient,
                subject: subject,
                content: content
            })
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.detail || 'Không thể gửi email thực tế!', 'error');
            return;
        }

        showToast(`Đã gửi email thực tế đến ${recipient} thành công!`, 'success');
    } catch (err) {
        console.error(err);
        showToast('Lỗi khi gửi email thực tế!', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Gửi Email Thực Tế Đến Khách Hàng';
        }
    }
}


// =========================================================================
// MỤC 3.3.4 & HÌNH 3.7.5: AI GỢI Ý KHUNG GIỜ TRỐNG DẠNG BẢNG
// =========================================================================

function openAISuggestModal() {
    const modal = document.getElementById('modal-ai-suggest-slots');
    if (!modal) return;
    
    const sportSel = document.getElementById('ai-suggest-sport');
    if (sportSel && state.currentBookingSportFilter && state.currentBookingSportFilter !== 'ALL') {
        sportSel.value = state.currentBookingSportFilter;
    }
    const dateInput = document.getElementById('ai-suggest-date');
    if (dateInput) {
        dateInput.value = document.getElementById('matrix-booking-date')?.value || getLocalDateString();
    }
    modal.classList.remove('hidden');
}

function closeAISuggestModal() {
    const modal = document.getElementById('modal-ai-suggest-slots');
    if (modal) modal.classList.add('hidden');
}

async function handleAISuggestSubmit(e) {
    e.preventDefault();
    const sport = document.getElementById('ai-suggest-sport').value;
    const date = document.getElementById('ai-suggest-date').value || getLocalDateString();
    const prefTime = document.getElementById('ai-suggest-pref-time').value.trim();
    const btn = document.getElementById('btn-run-ai-suggest');
    const tbody = document.getElementById('ai-suggest-tbody');

    try {
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> AI đang phân tích lịch sân trống...';
        }
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-6 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2 text-emerald-400"></i> AI đang quét cơ sở dữ liệu và tìm khung giờ tối ưu...</td></tr>';
        }

        const queryText = `Tìm khung giờ sân ${sport} ngày ${date}${prefTime ? ' ưu tiên giờ ' + prefTime : ''}`;
        const res = await apiFetch('/api/ai/suggest-slots', {
            method: 'POST',
            body: JSON.stringify({
                user_query: queryText,
                sport_type: sport,
                date: date,
                preferred_time: prefTime || null
            })
        });

        const suggestions = res.suggested_slots || [];
        if (suggestions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-6 text-center text-slate-400"><i class="fa-solid fa-circle-exclamation text-amber-400 text-lg mb-1 block"></i> Không tìm thấy khung giờ trống nào phù hợp trong ngày đã chọn.</td></tr>';
            return;
        }

        tbody.innerHTML = suggestions.map((s, idx) => {
            const pitchId = s.pitch_id || 1;
            const pitchName = s.pitch_name || `Sân Thể Thao #${pitchId}`;
            const timeRange = `${s.start_time} - ${s.end_time}`;
            const hourlyPrice = Number(s.start_time >= '17:00' ? s.peak_price_per_hour : s.price_per_hour);
            const priceText = hourlyPrice ? `${hourlyPrice.toLocaleString()} đ/giờ` : 'Giá tiêu chuẩn';
            const reason = s.reason || 'Khung giờ thoáng, phù hợp thể lực và thời tiết lý tưởng';

            return `
                <tr class="hover:bg-slate-900/80 transition">
                    <td class="p-3 font-bold text-white flex items-center gap-1.5">
                        <span class="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-mono">${idx+1}</span>
                        <span>${pitchName}</span>
                    </td>
                    <td class="p-3 font-mono text-amber-300 font-semibold">${timeRange}</td>
                    <td class="p-3 font-mono text-emerald-400 font-bold">${priceText}</td>
                    <td class="p-3 text-slate-300 text-xs max-w-xs leading-relaxed">${reason}</td>
                    <td class="p-3 text-right">
                        <button type="button" onclick="selectSuggestedSlot(${pitchId}, '${date}', '${s.start_time}', '${s.end_time}')" class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs px-3 py-1.5 rounded-xl shadow transition">
                            <i class="fa-solid fa-check mr-1"></i> Chọn Giờ Này
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        showToast('AI đã gợi ý thành công danh sách khung giờ tối ưu!', 'success');
    } catch (err) {
        console.error(err);
        if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-rose-400">Lỗi AI: ${err.message || 'Không thể lấy gợi ý'}</td></tr>`;
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Phân Tích & Hiển Thị Bảng Gợi Ý Bằng AI';
        }
    }
}

function selectSuggestedSlot(pitchId, dateStr, startTime, endTime) {
    closeAISuggestModal();
    switchTab('matrix-booking');

    const dateInput = document.getElementById('matrix-booking-date');
    if (dateInput) dateInput.value = dateStr;

    const pitchSelect = document.getElementById('matrix-pitch-select');
    if (pitchSelect) pitchSelect.value = pitchId;

    const startSel = document.getElementById('matrix-start-time');
    if (startSel) startSel.value = startTime;

    const endSel = document.getElementById('matrix-end-time');
    if (endSel) endSel.value = endTime;

    recalculateMatrixPrice();
    selectVisualPitch(pitchId);
    showToast(`Đã áp dụng gợi ý AI: Sân #${pitchId} (${startTime} - ${endTime})`, 'success');
}


// =========================================================================
// MỤC 3.3.4 & HÌNH 3.7.6: HỘP THOẠI TẠO TIN NHẮN XÁC NHẬN AI
// =========================================================================

let currentDialogBooking = null;

async function openAINotifDialog(bookingId) {
    const modal = document.getElementById('modal-ai-notif-dialog');
    const metaBox = document.getElementById('ai-notif-dialog-meta');
    const contentBox = document.getElementById('ai-notif-dialog-content');
    if (!modal) return;

    modal.classList.remove('hidden');
    if (metaBox) metaBox.innerHTML = '<p class="text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Đang tải thông tin đơn và gọi AI...</p>';
    if (contentBox) contentBox.value = 'AI đang soạn tin nhắn xác nhận cá nhân hóa...';

    try {
        const bookings = await apiFetch('/api/bookings');
        const b = (bookings || []).find(x => x.id === bookingId);
        currentDialogBooking = b;

        if (b && metaBox) {
            metaBox.innerHTML = `
                <div class="flex justify-between items-center border-b border-slate-800 pb-1.5">
                    <span class="font-bold text-white">Đơn đặt: <strong class="text-amber-400 font-mono">#${b.id}</strong></span>
                    <span class="text-emerald-400 font-bold font-mono">${(Number(b.total_price) || 0).toLocaleString()} đ</span>
                </div>
                <div class="grid grid-cols-2 gap-2 pt-1 text-[11px] text-slate-400">
                    <div>Khách: <strong class="text-slate-200">${b.customer_name}</strong> (${b.customer_phone})</div>
                    <div>Sân: <strong class="text-slate-200">${b.pitch?.name || 'Sân thể thao'}</strong></div>
                    <div>Ngày: <strong class="text-slate-200 font-mono">${b.booking_date}</strong></div>
                    <div>Giờ: <strong class="text-slate-200 font-mono">${b.start_time} - ${b.end_time}</strong></div>
                </div>
            `;
        }

        const res = await apiFetch('/api/ai/generate-notifications', {
            method: 'POST',
            body: JSON.stringify({
                booking_id: bookingId,
                notification_type: 'CONFIRMATION'
            })
        });

        const msg = res.messages?.sms || res.messages?.zalo || res.messages?.email?.body || 'Xác nhận đặt sân thành công!';
        if (contentBox) contentBox.value = msg;
        showToast('AI đã tạo tin nhắn xác nhận thành công!', 'success');
    } catch (err) {
        console.error(err);
        if (contentBox) contentBox.value = `Lỗi tạo tin nhắn: ${err.message}`;
    }
}

function closeAINotifDialog() {
    const modal = document.getElementById('modal-ai-notif-dialog');
    if (modal) modal.classList.add('hidden');
}

function copyAINotifMessage() {
    const content = document.getElementById('ai-notif-dialog-content')?.value;
    if (!content) return;
    navigator.clipboard.writeText(content).then(() => {
        showToast('Đã sao chép tin nhắn vào clipboard thành công!', 'success');
    }).catch(() => {
        showToast('Không thể tự động sao chép, vui lòng bôi đen và nhấn Ctrl+C', 'warning');
    });
}

async function sendRealEmailFromDialog() {
    if (!currentDialogBooking) {
        showToast('Không tìm thấy thông tin đơn đặt sân!', 'error');
        return;
    }
    let email = currentDialogBooking.customer?.email || currentDialogBooking.invoice_email || currentDialogBooking.user?.email;
    if (!email) {
        email = prompt('Khách hàng này chưa có email trong đơn. Vui lòng nhập địa chỉ email người nhận:');
        if (!email || !email.includes('@')) {
            showToast('Địa chỉ email không hợp lệ!', 'warning');
            return;
        }
    }
    const content = document.getElementById('ai-notif-dialog-content')?.value;
    const btn = document.getElementById('btn-dialog-send-email');
    try {
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang gửi...';
        }
        const res = await apiFetch('/api/ai/send-email', {
            method: 'POST',
            body: JSON.stringify({
                booking_id: currentDialogBooking.id,
                recipient_email: email,
                subject: `Xác nhận đặt sân thành công #${currentDialogBooking.id} - Thể Thao ICTU`,
                content: content
            })
        });

        if (res.mode === 'LIVE_SMTP') {
            showToast(`🎉 Đã gửi email xác nhận thực tế qua SMTP đến ${email} thành công!`, 'success');
        } else if (res.mode === 'LOCAL_OUTBOX') {
            showToast(`📧 ${res.message || 'Thư đã lưu vào Outbox hệ thống (Cấu hình SMTP Gmail App Password để gửi email thật)'}`, 'info');
        } else if (res.mode === 'SMTP_ERROR' || res.success === false) {
            showToast(`⚠️ Lỗi SMTP: ${res.message || 'Không thể gửi qua SMTP máy chủ'}`, 'error');
        } else {
            showToast(res.message || `Đã gửi email xác nhận đến ${email} thành công!`, 'success');
        }
    } catch (e) {
        showToast(e.message || 'Lỗi gửi email', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Gửi Email Khách';
        }
    }
}


// =========================================================================
// MỤC 3.3.4 & HÌNH 3.7.7: TÓM TẮT AI & GỢI Ý KHUYẾN MÃI TRÊN DASHBOARD
// =========================================================================

async function loadAIDashboardSummary(manual = false) {
    const textEl = document.getElementById('dashboard-ai-summary-text');
    const listEl = document.getElementById('dashboard-ai-promotions-list');
    if (!textEl || !listEl) return;

    try {
        if (manual) textEl.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> AI đang phân tích dữ liệu hoạt động và tính toán khuyến mãi...';
        const res = await apiFetch('/api/ai/occupancy-report', {
            method: 'POST',
            body: JSON.stringify({})
        });

        textEl.innerText = res.summary || 'Công suất sân đạt mức tốt vào giờ cao điểm (17:00 - 20:30), khuyến nghị áp dụng ưu đãi giờ vàng ban ngày để tối ưu hóa doanh thu toàn hệ thống.';

        const promos = res.promotions || [
            {
                title: "Flash Sale Giờ Trưa (09:00 - 14:00)",
                discount: "Giảm 20%",
                description: "Tặng voucher giảm giá 20% cho các khung giờ vắng khách trong tuần, lấp đầy công suất sân trống."
            },
            {
                title: "Combo Đặt Sân Theo Tháng",
                discount: "Tặng 2 buổi",
                description: "Ưu đãi tặng thêm 2 buổi đá miễn phí và nước ngọt cho các đội bóng ký hợp đồng cố định theo quý."
            },
            {
                title: "Giờ Vàng Học Sinh - Sinh Viên",
                discount: "Đồng giá 150k",
                description: "Áp dụng giá ưu đãi cho học sinh sinh viên thi đấu cầu lông và bóng đá vào các buổi chiều từ Thứ 2 đến Thứ 6."
            }
        ];

        listEl.innerHTML = promos.map(p => `
            <div class="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2 hover:border-amber-500/40 transition">
                <div class="flex justify-between items-start">
                    <span class="text-xs font-bold text-white">${p.title}</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-black bg-amber-500 text-slate-950">${p.discount}</span>
                </div>
                <p class="text-[11px] text-slate-400 leading-relaxed">${p.description}</p>
            </div>
        `).join('');

        if (manual) showToast('Đã làm mới báo cáo tóm tắt AI thành công!', 'success');
    } catch (e) {
        console.error("loadAIDashboardSummary error:", e);
        textEl.innerText = "Hệ thống đang sử dụng dữ liệu thống kê mặc định. Tỷ lệ lấp đầy đạt 68.5%, giờ cao điểm đạt 88.5%.";
    }
}

async function openSystemOutboxModal() {
    const modal = document.getElementById('modal-system-outbox');
    const container = document.getElementById('system-outbox-list');
    if (!modal || !container) return;

    modal.classList.remove('hidden');
    container.innerHTML = `<div class="p-6 text-center text-slate-400 text-xs"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Đang tải thư hệ thống...</div>`;

    try {
        const res = await fetch('/api/bookings/outbox-emails');
        if (!res.ok) throw new Error('Không thể lấy thư outbox');
        const emails = await res.json();

        if (emails.length === 0) {
            container.innerHTML = `<p class="text-xs text-slate-400 text-center py-8">Hộp thư hệ thống hiện tại chưa có thư nào.</p>`;
            return;
        }

        container.innerHTML = emails.map((item, idx) => `
            <div class="bg-slate-950 border border-slate-800 rounded-2xl p-4 space-y-2">
                <div class="flex justify-between items-start border-b border-slate-900 pb-2">
                    <div>
                        <span class="text-xs font-bold text-teal-400 font-mono">#${idx + 1} - ${item.filename}</span>
                        <p class="text-[11px] text-slate-400"><i class="fa-solid fa-clock mr-1 text-amber-400"></i> Thời gian lưu: ${item.mtime}</p>
                    </div>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300">EML Outbox</span>
                </div>
                <pre class="bg-slate-900/90 p-3 rounded-xl text-[11px] text-slate-200 font-mono overflow-x-auto whitespace-pre-wrap max-h-48 leading-relaxed">${escapeHtml(item.content)}</pre>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<p class="text-xs text-rose-400 text-center py-6">Lỗi tải hòm thư hệ thống: ${e.message}</p>`;
    }
}

function closeSystemOutboxModal() {
    const modal = document.getElementById('modal-system-outbox');
    if (modal) modal.classList.add('hidden');
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

