/* ===================================================================
   ADMIN SETTINGS PAGE - JAVASCRIPT
   Save this as: static/js/admin-settings.js
   ================================================================ */

(function () {
  "use strict";

  // ============ KHỞI TẠO KHI TRANG TẢI XONG ============
  document.addEventListener("DOMContentLoaded", function () {
    initTabNavigation();
    initColorPicker();
    initImagePreview();
    initUnsavedChanges();
    initFormValidation();
    initAutoSave();
    initTooltips();
  });

  // ============ QUẢN LÝ ĐIỀU HƯỚNG TAB ============
  // Xử lý chuyển đổi giữa các tab và lưu trạng thái vào localStorage
  function initTabNavigation() {
    const tabs = document.querySelectorAll(".settings-tab");
    const tabPanes = document.querySelectorAll(".tab-pane");

    // Khôi phục tab đã chọn từ localStorage
    const savedTab = localStorage.getItem("activeSettingsTab") || "general";
    activateTab(savedTab);

    tabs.forEach((tab) => {
      tab.addEventListener("click", function () {
        const targetId = this.getAttribute("data-bs-target").substring(1);
        activateTab(targetId);
        // Lưu tab hiện tại vào localStorage
        localStorage.setItem("activeSettingsTab", targetId);
      });
    });

    function activateTab(tabId) {
      // Xóa active class khỏi tất cả tabs
      tabs.forEach((t) => t.classList.remove("active"));
      tabPanes.forEach((p) => {
        p.classList.remove("show", "active");
      });

      // Thêm active class cho tab được chọn
      const activeTab = document.querySelector(`[data-bs-target="#${tabId}"]`);
      const activePane = document.getElementById(tabId);

      if (activeTab && activePane) {
        activeTab.classList.add("active");
        activePane.classList.add("show", "active");

        // Hiệu ứng fade in mượt mà
        activePane.style.opacity = "0";
        setTimeout(() => {
          activePane.style.transition = "opacity 0.3s ease-in-out";
          activePane.style.opacity = "1";
        }, 10);
      }
    }
  }

  // ============ BỘ CHỌN MÀU VÀ PREVIEW ============
  // Hiển thị preview màu đã chọn và cập nhật giá trị hex
  function initColorPicker() {
    const colorInput = document.getElementById("primaryColorInput");
    if (!colorInput) return;

    const colorPreview = document.getElementById("colorPreview");
    const colorValue = document.getElementById("colorValue");

    // Hàm cập nhật preview màu
    function updateColorPreview(color) {
      if (colorPreview) {
        colorPreview.style.backgroundColor = color;
        // Thêm hiệu ứng animation khi thay đổi màu
        colorPreview.style.transform = "scale(1.1)";
        setTimeout(() => {
          colorPreview.style.transform = "scale(1)";
        }, 200);
      }
      if (colorValue) {
        colorValue.textContent = color.toUpperCase();
      }
    }

    // Khởi tạo màu ban đầu
    if (colorInput.value) {
      updateColorPreview(colorInput.value);
    }

    // Lắng nghe sự kiện thay đổi màu
    colorInput.addEventListener("input", function () {
      updateColorPreview(this.value);
    });

    // Lắng nghe sự kiện change (khi người dùng đóng color picker)
    colorInput.addEventListener("change", function () {
      updateColorPreview(this.value);
      showNotification("Màu đã được cập nhật", "info");
    });
  }

  // ============ PREVIEW ẢNH KHI UPLOAD ============
  // Hiển thị preview ảnh ngay khi người dùng chọn file
  function initImagePreview() {
    const imageInputs = [
      { input: "logo", preview: null },
      { input: "logo_chatbot", preview: null },
      { input: "favicon", preview: null },
      { input: "favicon_ico", preview: null },
      { input: "favicon_png", preview: null },
      { input: "favicon_svg", preview: null },
      { input: "apple_touch_icon", preview: null },
      { input: "default_share_image", preview: null },
    ];

    imageInputs.forEach((item) => {
      const input = document.querySelector(`input[name="${item.input}"]`);
      if (!input) return;

      input.addEventListener("change", function (e) {
        const file = e.target.files[0];
        if (!file) return;

        // Kiểm tra loại file
        if (!file.type.startsWith("image/")) {
          showNotification("Vui lòng chọn file ảnh hợp lệ", "error");
          this.value = "";
          return;
        }

        // Kiểm tra kích thước file (max 5MB)
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
          showNotification("Kích thước ảnh không được vượt quá 5MB", "error");
          this.value = "";
          return;
        }

        // Đọc và hiển thị preview
        const reader = new FileReader();
        reader.onload = function (event) {
          createOrUpdatePreview(input, event.target.result, file.name);
        };
        reader.readAsDataURL(file);
      });
    });

    // Tạo hoặc cập nhật preview ảnh
    function createOrUpdatePreview(input, imageSrc, fileName) {
      const formGroup = input.closest(".settings-form-group");
      let previewContainer = formGroup.querySelector(".settings-image-preview");

      // Nếu chưa có preview container, tạo mới
      if (!previewContainer) {
        previewContainer = document.createElement("div");
        previewContainer.className = "settings-image-preview";
        input.parentNode.insertBefore(previewContainer, input.nextSibling);
      }

      // Xác định class cho preview dựa trên loại input
      let imgClass = "settings-preview-img";
      if (input.name === "favicon") {
        imgClass = "settings-preview-favicon";
      }

      // Cập nhật nội dung preview với nút xóa
      previewContainer.innerHTML = `
                <div style="position: relative; display: inline-block;">
                    <img src="${imageSrc}" alt="Preview" class="${imgClass}" style="max-width: 300px;">
                    <button type="button" class="remove-preview-btn" title="Xóa ảnh">
                        <i class="bi bi-x-circle-fill"></i>
                    </button>
                    <div class="preview-filename">${fileName}</div>
                </div>
            `;

      // Thêm hiệu ứng fade in
      previewContainer.style.opacity = "0";
      setTimeout(() => {
        previewContainer.style.transition = "opacity 0.3s ease-in-out";
        previewContainer.style.opacity = "1";
      }, 10);

      // Xử lý nút xóa preview
      const removeBtn = previewContainer.querySelector(".remove-preview-btn");
      removeBtn.addEventListener("click", function () {
        input.value = "";
        previewContainer.style.opacity = "0";
        setTimeout(() => {
          previewContainer.remove();
        }, 300);
        showNotification("Đã xóa ảnh preview", "info");
      });

      showNotification("Ảnh đã được tải lên", "success");
    }

    // Thêm CSS cho nút xóa và tên file (inline để tránh xung đột)
    if (!document.getElementById("preview-styles")) {
      const style = document.createElement("style");
      style.id = "preview-styles";
      style.textContent = `
                .remove-preview-btn {
                    position: absolute;
                    top: -10px;
                    right: -10px;
                    background: #ef4444;
                    color: white;
                    border: 2px solid white;
                    border-radius: 50%;
                    width: 32px;
                    height: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                .remove-preview-btn:hover {
                    background: #dc2626;
                    transform: scale(1.1);
                }
                .remove-preview-btn i {
                    font-size: 1.2rem;
                }
                .preview-filename {
                    margin-top: 0.5rem;
                    font-size: 0.85rem;
                    color: #6b7280;
                    text-align: center;
                    font-weight: 500;
                }
            `;
      document.head.appendChild(style);
    }
  }

  // ============ THEO DÕI THAY ĐỔI CHƯA LƯU ============
  // Cảnh báo người dùng khi rời trang với dữ liệu chưa lưu
  function initUnsavedChanges() {
    const form = document.querySelector(".settings-card form");
    if (!form) return;

    let isFormChanged = false;
    let isSubmitting = false;
    const cancelBtn = document.querySelector(".settings-btn-secondary");
    const submitBtn = document.querySelector(".settings-btn-primary");
    const actionsContainer = document.querySelector(".settings-actions");

    // Ẩn cả container chứa 2 nút ban đầu
    if (actionsContainer) {
      actionsContainer.style.display = "none";
    }

    // Theo dõi tất cả các input trong form
    const inputs = form.querySelectorAll("input, textarea, select");
    inputs.forEach((input) => {
      input.addEventListener("change", function () {
        if (!isSubmitting) {
          isFormChanged = true;
          showUnsavedBadge();
          showActionButtons();
        }
      });

      // Theo dõi typing cho textarea và text input
      if (
        input.type === "text" ||
        input.type === "email" ||
        input.tagName === "TEXTAREA"
      ) {
        input.addEventListener(
          "input",
          debounce(function () {
            if (!isSubmitting) {
              isFormChanged = true;
              showUnsavedBadge();
              showActionButtons();
            }
          }, 500)
        );
      }
    });

    // Hiển thị cả 2 nút khi có thay đổi
    function showActionButtons() {
      if (actionsContainer && actionsContainer.style.display === "none") {
        actionsContainer.style.display = "flex";
        actionsContainer.style.animation = "slideUpFade 0.4s ease-out";
      }
    }

    // Ẩn cả 2 nút khi không có thay đổi
    function hideActionButtons() {
      if (actionsContainer) {
        actionsContainer.style.animation = "slideDownFade 0.3s ease-out";
        setTimeout(() => {
          actionsContainer.style.display = "none";
        }, 300);
      }
    }

    // Thêm CSS animation cho action buttons
    if (!document.getElementById("action-buttons-animation")) {
      const style = document.createElement("style");
      style.id = "action-buttons-animation";
      style.textContent = `
            @keyframes slideUpFade {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            @keyframes slideDownFade {
                from {
                    opacity: 1;
                    transform: translateY(0);
                }
                to {
                    opacity: 0;
                    transform: translateY(20px);
                }
            }
        `;
      document.head.appendChild(style);
    }

    // Xử lý khi submit form
    form.addEventListener("submit", function () {
      isSubmitting = true;
      isFormChanged = false;
      hideUnsavedBadge();
      // Không ẩn nút khi submit để người dùng thấy nút đang loading
    });

    // Xử lý khi click nút hủy - reload trang
    if (cancelBtn) {
      cancelBtn.addEventListener("click", function (e) {
        e.preventDefault();
        if (
          confirm("Bạn có chắc muốn hủy các thay đổi? Trang sẽ được tải lại.")
        ) {
          location.reload();
        }
      });
    }

    // Cảnh báo khi rời trang
    window.addEventListener("beforeunload", function (e) {
      if (isFormChanged && !isSubmitting) {
        e.preventDefault();
        e.returnValue =
          "Bạn có thay đổi chưa lưu. Bạn có chắc muốn rời khỏi trang?";
        return e.returnValue;
      }
    });

    // Hiển thị badge "Chưa lưu"
    function showUnsavedBadge() {
      let badge = document.getElementById("unsaved-badge");
      if (!badge) {
        badge = document.createElement("div");
        badge.id = "unsaved-badge";
        badge.innerHTML = `
                <i class="bi bi-exclamation-circle"></i>
                <span>Có thay đổi chưa lưu</span>
            `;
        document.body.appendChild(badge);

        // Thêm CSS cho badge
        if (!document.getElementById("unsaved-badge-styles")) {
          const style = document.createElement("style");
          style.id = "unsaved-badge-styles";
          style.textContent = `
                    #unsaved-badge {
                        position: fixed;
                        bottom: 2rem;
                        left: 50%;
                        transform: translateX(-50%);
                        background: linear-gradient(135deg, #f59e0b, #d97706);
                        color: white;
                        padding: 0.75rem 1.5rem;
                        border-radius: 50px;
                        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        font-weight: 600;
                        z-index: 9999;
                        animation: slideUp 0.3s ease-out;
                    }
                    #unsaved-badge i {
                        font-size: 1.2rem;
                        animation: pulse 2s ease-in-out infinite;
                    }
                    @keyframes slideUp {
                        from {
                            transform: translateX(-50%) translateY(100px);
                            opacity: 0;
                        }
                        to {
                            transform: translateX(-50%) translateY(0);
                            opacity: 1;
                        }
                    }
                    @keyframes pulse {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0.5; }
                    }
                `;
          document.head.appendChild(style);
        }
      }
      badge.style.display = "flex";
    }

    // Ẩn badge
    function hideUnsavedBadge() {
      const badge = document.getElementById("unsaved-badge");
      if (badge) {
        badge.style.animation = "slideDown 0.3s ease-out";
        setTimeout(() => {
          badge.style.display = "none";
        }, 300);
      }
    }

    // Thêm animation slideDown
    if (!document.getElementById("slidedown-animation")) {
      const style = document.createElement("style");
      style.id = "slidedown-animation";
      style.textContent = `
            @keyframes slideDown {
                from {
                    transform: translateX(-50%) translateY(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(-50%) translateY(100px);
                    opacity: 0;
                }
            }
        `;
      document.head.appendChild(style);
    }
  }

  // ============ VALIDATION FORM THỜI GIAN THỰC ============
  // Kiểm tra và hiển thị lỗi validation ngay khi người dùng nhập
  function initFormValidation() {
    const form = document.querySelector(".settings-card form");
    if (!form) return;

    // Validation cho email
    const emailInputs = form.querySelectorAll('input[type="email"]');
    emailInputs.forEach((input) => {
      input.addEventListener("blur", function () {
        validateEmail(this);
      });
    });

    // Validation cho URL
    const urlInputs = form.querySelectorAll(
      'input[name$="_url"], input[name="main_url"]'
    );
    urlInputs.forEach((input) => {
      input.addEventListener("blur", function () {
        if (this.value) {
          validateURL(this);
        }
      });
    });

    // Validation cho số
    const numberInputs = form.querySelectorAll('input[type="number"]');
    numberInputs.forEach((input) => {
      input.addEventListener("blur", function () {
        validateNumber(this);
      });
    });

    function validateEmail(input) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (input.value && !emailRegex.test(input.value)) {
        showFieldError(input, "Email không hợp lệ");
        return false;
      } else {
        clearFieldError(input);
        return true;
      }
    }

    function validateURL(input) {
      try {
        new URL(input.value);
        clearFieldError(input);
        return true;
      } catch (e) {
        showFieldError(input, "URL không hợp lệ");
        return false;
      }
    }

    function validateNumber(input) {
      const value = parseInt(input.value);
      const min = parseInt(input.min);
      const max = parseInt(input.max);

      if (isNaN(value)) {
        showFieldError(input, "Vui lòng nhập số hợp lệ");
        return false;
      }
      if (min && value < min) {
        showFieldError(input, `Giá trị tối thiểu là ${min}`);
        return false;
      }
      if (max && value > max) {
        showFieldError(input, `Giá trị tối đa là ${max}`);
        return false;
      }
      clearFieldError(input);
      return true;
    }

    function showFieldError(input, message) {
      clearFieldError(input);
      input.classList.add("is-invalid");
      const errorDiv = document.createElement("div");
      errorDiv.className = "field-error-message";
      errorDiv.textContent = message;
      input.parentNode.appendChild(errorDiv);

      // Thêm CSS cho error message nếu chưa có
      if (!document.getElementById("field-error-styles")) {
        const style = document.createElement("style");
        style.id = "field-error-styles";
        style.textContent = `
                    .is-invalid {
                        border-color: #ef4444 !important;
                    }
                    .field-error-message {
                        color: #ef4444;
                        font-size: 0.85rem;
                        margin-top: 0.25rem;
                        display: flex;
                        align-items: center;
                        gap: 0.25rem;
                        animation: fadeIn 0.2s ease-in;
                    }
                    .field-error-message::before {
                        content: "⚠";
                        font-size: 1rem;
                    }
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(-5px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                `;
        document.head.appendChild(style);
      }
    }

    function clearFieldError(input) {
      input.classList.remove("is-invalid");
      const errorMsg = input.parentNode.querySelector(".field-error-message");
      if (errorMsg) {
        errorMsg.remove();
      }
    }
  }

  // ============ TỰ ĐỘNG LƯU BẢN NHÁP (OPTIONAL) ============
  // Tự động lưu dữ liệu form vào localStorage mỗi 30 giây
  // Có thể xóa chức năng này nếu không cần thiết
  //    function initAutoSave() {
  //        const form = document.querySelector('.settings-card form');
  //        if (!form) return;
  //
  //        const AUTO_SAVE_KEY = 'settings_autosave';
  //        const AUTO_SAVE_INTERVAL = 30000; // 30 giây
  //
  //        // Khôi phục dữ liệu đã lưu
  //        restoreAutoSave();
  //
  //        // Tự động lưu định kỳ
  //        setInterval(function() {
  //            saveFormData();
  //        }, AUTO_SAVE_INTERVAL);
  //
  //        function saveFormData() {
  //            const formData = new FormData(form);
  //            const data = {};
  //
  //            // Chỉ lưu text fields, không lưu files
  //            for (let [key, value] of formData.entries()) {
  //                const input = form.querySelector(`[name="${key}"]`);
  //                if (input && input.type !== 'file' && input.type !== 'hidden') {
  //                    data[key] = value;
  //                }
  //            }
  //
  //            localStorage.setItem(AUTO_SAVE_KEY, JSON.stringify({
  //                data: data,
  //                timestamp: new Date().toISOString()
  //            }));
  //        }
  //
  //        function restoreAutoSave() {
  //            const saved = localStorage.getItem(AUTO_SAVE_KEY);
  //            if (!saved) return;
  //
  //            try {
  //                const { data, timestamp } = JSON.parse(saved);
  //                const savedDate = new Date(timestamp);
  //                const now = new Date();
  //                const hoursDiff = (now - savedDate) / (1000 * 60 * 60);
  //
  //                // Chỉ khôi phục nếu dữ liệu được lưu trong vòng 24 giờ
  //                if (hoursDiff > 24) {
  //                    localStorage.removeItem(AUTO_SAVE_KEY);
  //                    return;
  //                }
  //
  //                // Hiển thị thông báo xác nhận khôi phục
  //                if (confirm(`Tìm thấy bản lưu tự động từ ${savedDate.toLocaleString('vi-VN')}. Bạn có muốn khôi phục không?`)) {
  //                    Object.keys(data).forEach(key => {
  //                        const input = form.querySelector(`[name="${key}"]`);
  //                        if (input && input.type !== 'file') {
  //                            input.value = data[key];
  //                        }
  //                    });
  //                    showNotification('Đã khôi phục bản lưu tự động', 'success');
  //                } else {
  //                    localStorage.removeItem(AUTO_SAVE_KEY);
  //                }
  //            } catch (e) {
  //                console.error('Error restoring autosave:', e);
  //                localStorage.removeItem(AUTO_SAVE_KEY);
  //            }
  //        }
  //
  //        // Xóa autosave khi submit thành công
  //        form.addEventListener('submit', function() {
  //            localStorage.removeItem(AUTO_SAVE_KEY);
  //        });
  //    }

  // ============ TOOLTIPS (OPTIONAL) ============
  // Hiển thị tooltips cho các icon và help text
  // Có thể xóa nếu không cần
  function initTooltips() {
    const tooltipElements = document.querySelectorAll("[title]");

    tooltipElements.forEach((element) => {
      element.addEventListener("mouseenter", function (e) {
        showTooltip(this, this.getAttribute("title"));
      });

      element.addEventListener("mouseleave", function () {
        hideTooltip();
      });
    });

    function showTooltip(element, text) {
      hideTooltip(); // Xóa tooltip cũ nếu có

      const tooltip = document.createElement("div");
      tooltip.id = "custom-tooltip";
      tooltip.textContent = text;
      document.body.appendChild(tooltip);

      const rect = element.getBoundingClientRect();
      const tooltipRect = tooltip.getBoundingClientRect();

      // Tính toán vị trí
      let top = rect.top - tooltipRect.height - 10;
      let left = rect.left + rect.width / 2 - tooltipRect.width / 2;

      // Đảm bảo tooltip không ra ngoài viewport
      if (top < 0) {
        top = rect.bottom + 10;
      }
      if (left < 0) {
        left = 10;
      }
      if (left + tooltipRect.width > window.innerWidth) {
        left = window.innerWidth - tooltipRect.width - 10;
      }

      tooltip.style.top = top + window.scrollY + "px";
      tooltip.style.left = left + "px";

      // Thêm CSS nếu chưa có
      if (!document.getElementById("tooltip-styles")) {
        const style = document.createElement("style");
        style.id = "tooltip-styles";
        style.textContent = `
                    #custom-tooltip {
                        position: absolute;
                        background: #1f2937;
                        color: white;
                        padding: 0.5rem 0.75rem;
                        border-radius: 6px;
                        font-size: 0.85rem;
                        z-index: 10000;
                        pointer-events: none;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                        animation: tooltipFadeIn 0.2s ease-out;
                        max-width: 250px;
                    }
                    @keyframes tooltipFadeIn {
                        from { opacity: 0; transform: translateY(-5px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                `;
        document.head.appendChild(style);
      }
    }

    function hideTooltip() {
      const tooltip = document.getElementById("custom-tooltip");
      if (tooltip) {
        tooltip.remove();
      }
    }
  }

  // ============ HÀM TIỆN ÍCH ============

  // Debounce function - Trì hoãn thực thi hàm
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // Hiển thị thông báo
  function showNotification(message, type = "info") {
    // Xóa notification cũ nếu có
    const oldNotification = document.querySelector(".settings-notification");
    if (oldNotification) {
      oldNotification.remove();
    }

    const notification = document.createElement("div");
    notification.className = `settings-notification settings-notification-${type}`;

    const icon =
      {
        success: "check-circle-fill",
        error: "x-circle-fill",
        warning: "exclamation-triangle-fill",
        info: "info-circle-fill",
      }[type] || "info-circle-fill";

    notification.innerHTML = `
            <i class="bi bi-${icon}"></i>
            <span>${message}</span>
        `;

    document.body.appendChild(notification);

    // Tự động ẩn sau 3 giây
    setTimeout(() => {
      notification.style.animation = "notificationSlideOut 0.3s ease-out";
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 3000);

    // Thêm CSS cho notification nếu chưa có
    if (!document.getElementById("notification-styles")) {
      const style = document.createElement("style");
      style.id = "notification-styles";
      style.textContent = `
                .settings-notification {
                    position: fixed;
                    top: 2rem;
                    right: 2rem;
                    padding: 1rem 1.5rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    z-index: 10000;
                    font-weight: 500;
                    animation: notificationSlideIn 0.3s ease-out;
                    min-width: 300px;
                }
                .settings-notification i {
                    font-size: 1.5rem;
                }
                .settings-notification-success {
                    background: #10b981;
                    color: white;
                }
                .settings-notification-error {
                    background: #ef4444;
                    color: white;
                }
                .settings-notification-warning {
                    background: #f59e0b;
                    color: white;
                }
                .settings-notification-info {
                    background: #3b82f6;
                    color: white;
                }
                @keyframes notificationSlideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes notificationSlideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                }
                @media (max-width: 576px) {
                    .settings-notification {
                        top: 1rem;
                        right: 1rem;
                        left: 1rem;
                        min-width: auto;
                    }
                }
            `;
      document.head.appendChild(style);
    }
  }
})();
