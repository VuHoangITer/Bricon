window.addEventListener("scroll", function () {
  const floatingButtons = document.querySelector(".floating-buttons");
  if (floatingButtons) {
    floatingButtons.style.display = "flex"; // luôn hiển thị
  }
});

// ==================== ANIMATE ON SCROLL ====================
const observerOptions = {
  threshold: 0.1,
  rootMargin: "0px 0px -50px 0px",
};

const observer = new IntersectionObserver(function (entries) {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("animate-on-scroll");
    }
  });
}, observerOptions);

// Observe all product cards and blog cards
document.addEventListener("DOMContentLoaded", function () {
  const cards = document.querySelectorAll(".product-card, .blog-card");
  cards.forEach((card) => {
    observer.observe(card);
  });
});

// ==================== AUTO DISMISS ALERTS ====================
document.addEventListener("DOMContentLoaded", function () {
  // Chỉ đóng alerts có nút close (alert-dismissible), không đóng các alert tĩnh
  const alerts = document.querySelectorAll(".alert.alert-dismissible");
  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000); // Auto close after 5 seconds
  });
});

// ==================== SEARCH FORM VALIDATION ====================
document.addEventListener("DOMContentLoaded", function () {
  const searchForms = document.querySelectorAll('form[action*="search"]');
  searchForms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      const input = form.querySelector('input[name="q"], input[name="search"]');
      if (input && input.value.trim() === "") {
        e.preventDefault();
        alert("Vui lòng nhập từ khóa tìm kiếm");
      }
    });
  });
});

// ==================== IMAGE LAZY LOADING ====================
if ("loading" in HTMLImageElement.prototype) {
  const images = document.querySelectorAll("img[data-src]");
  images.forEach((img) => {
    img.src = img.dataset.src;
  });
} else {
  // Fallback for browsers that don't support lazy loading
  const script = document.createElement("script");
  script.src =
    "https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js";
  document.body.appendChild(script);
}
// ==================== BANNER AUTO SLIDE ====================
document.addEventListener("DOMContentLoaded", function () {
  const slides = document.querySelectorAll(".swiper-slide");
  let currentIndex = 0;

  if (slides.length > 0) {
    // Ẩn hết, chỉ hiện slide đầu tiên
    slides.forEach((slide, index) => {
      slide.style.display = index === 0 ? "block" : "none";
    });

    // Hàm đổi slide
    function showNextSlide() {
      slides[currentIndex].style.display = "none";
      currentIndex = (currentIndex + 1) % slides.length;
      slides[currentIndex].style.display = "block";
    }

    // Gọi interval chạy đều mỗi 1 giây
    setInterval(showNextSlide, 1000);
  }
});
// ==================== SMOOTH SCROLL - FIXED ====================
// Chỉ áp dụng cho links KHÔNG phải Bootstrap tabs
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll('a[href*="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      // BỎ QUA nếu là Bootstrap tab hoặc có data-bs-toggle
      if (this.hasAttribute("data-bs-toggle")) {
        return;
      }

      const href = this.getAttribute("href");

      // BỎ QUA nếu href chỉ là "#" đơn thuần
      if (href === "#") {
        return;
      }

      // Kiểm tra nếu target element tồn tại
      const targetId = href.includes("#") ? href.split("#")[1] : null;

      if (targetId) {
        const target = document.getElementById(targetId);

        // Chỉ scroll nếu element thực sự tồn tại
        if (target) {
          e.preventDefault();
          const offsetTop = target.offsetTop - 120;
          window.scrollTo({
            top: offsetTop,
            behavior: "smooth",
          });
        }
      }
    });
  });
});
// ==================== SCROLL TO TOP WITH PROGRESS ====================
(function () {
  const scrollToTopBtn = document.getElementById("scrollToTop");
  if (!scrollToTopBtn) return;

  const progressCircle = scrollToTopBtn.querySelector("circle.progress");
  const radius = progressCircle.r.baseVal.value;
  const circumference = 2 * Math.PI * radius;

  // Set initial progress circle
  progressCircle.style.strokeDasharray = circumference;
  progressCircle.style.strokeDashoffset = circumference;

  // Update progress on scroll
  function updateProgress() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight =
      document.documentElement.scrollHeight -
      document.documentElement.clientHeight;
    const scrollPercentage = (scrollTop / scrollHeight) * 100;

    // Update progress circle
    const offset = circumference - (scrollPercentage / 100) * circumference;
    progressCircle.style.strokeDashoffset = offset;

    // Show/hide button
    if (scrollTop > 300) {
      scrollToTopBtn.classList.add("show");
    } else {
      scrollToTopBtn.classList.remove("show");
    }
  }

  // Smooth scroll to top
  scrollToTopBtn.addEventListener("click", function () {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  });

  // Listen to scroll event
  let ticking = false;
  window.addEventListener("scroll", function () {
    if (!ticking) {
      window.requestAnimationFrame(function () {
        updateProgress();
        ticking = false;
      });
      ticking = true;
    }
  });

  // Initial check
  updateProgress();
})();
