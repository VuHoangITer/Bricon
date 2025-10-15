// ==================== FLOATING BUTTONS ====================
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

// ==================== BANNER LAZY LOAD + RESPONSIVE (INTEGRATED) ====================
document.addEventListener('DOMContentLoaded', function() {
  const carousel = document.getElementById('bannerCarousel');
  if (!carousel) return; // Không có banner thì bỏ qua
  
  // ✅ 1. LAZY LOAD BANNER IMAGES
  const lazyBannerImages = carousel.querySelectorAll('.banner-img[loading="lazy"]');
  
  if ('IntersectionObserver' in window && lazyBannerImages.length > 0) {
    const bannerObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          const parent = img.closest('.carousel-item');
          
          // Add loading class for skeleton effect
          if (parent) parent.classList.add('loading');
          
          // Load image
          img.onload = function() {
            img.classList.add('loaded');
            if (parent) parent.classList.remove('loading');
            observer.unobserve(img);
          };
          
          // Trigger load if data-src exists
          if (img.dataset.src) {
            img.src = img.dataset.src;
          } else {
            img.classList.add('loaded'); // Image already has src
            if (parent) parent.classList.remove('loading');
          }
        }
      });
    }, {
      rootMargin: '100px' // Preload 100px before viewport
    });

    lazyBannerImages.forEach(img => bannerObserver.observe(img));
  } else {
    // Fallback: immediately mark as loaded
    lazyBannerImages.forEach(img => img.classList.add('loaded'));
  }

  // ✅ 2. PRELOAD ADJACENT SLIDES
  carousel.addEventListener('slide.bs.carousel', function(e) {
    const slides = carousel.querySelectorAll('.carousel-item');
    const nextIndex = e.to;
    
    // Preload current slide
    const currentSlide = slides[nextIndex];
    if (currentSlide) {
      const currentImg = currentSlide.querySelector('.banner-img');
      if (currentImg && !currentImg.classList.contains('loaded')) {
        currentImg.classList.add('loaded');
      }
    }

    // Preload adjacent slides (prev/next)
    const prevIndex = nextIndex - 1 < 0 ? slides.length - 1 : nextIndex - 1;
    const nextSlideIndex = nextIndex + 1 >= slides.length ? 0 : nextIndex + 1;
    
    [prevIndex, nextSlideIndex].forEach(index => {
      const slide = slides[index];
      if (slide) {
        const img = slide.querySelector('.banner-img');
        if (img && !img.classList.contains('loaded')) {
          img.classList.add('loaded');
        }
      }
    });
  });

  // ✅ 3. PAUSE ON HOVER (Desktop only)
  if (window.innerWidth >= 768) {
    let isHovering = false;
    
    carousel.addEventListener('mouseenter', function() {
      isHovering = true;
      const bsCarousel = bootstrap.Carousel.getInstance(carousel);
      if (bsCarousel) bsCarousel.pause();
    });
    
    carousel.addEventListener('mouseleave', function() {
      if (isHovering) {
        isHovering = false;
        const bsCarousel = bootstrap.Carousel.getInstance(carousel);
        if (bsCarousel) bsCarousel.cycle();
      }
    });
  }

  // ✅ 4. PAUSE ON TOUCH (Mobile)
  carousel.addEventListener('touchstart', function() {
    const bsCarousel = bootstrap.Carousel.getInstance(carousel);
    if (bsCarousel) bsCarousel.pause();
  });

  carousel.addEventListener('touchend', function() {
    const bsCarousel = bootstrap.Carousel.getInstance(carousel);
    if (bsCarousel) {
      setTimeout(() => bsCarousel.cycle(), 3000); // Resume after 3s
    }
  });

  // ✅ 5. KEYBOARD NAVIGATION
  carousel.addEventListener('keydown', function(e) {
    const bsCarousel = bootstrap.Carousel.getInstance(carousel);
    if (!bsCarousel) return;
    
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      bsCarousel.prev();
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      bsCarousel.next();
    }
  });

  // ✅ 6. RESPECT REDUCED MOTION
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    carousel.setAttribute('data-bs-interval', 'false');
    carousel.querySelectorAll('.carousel-item').forEach(item => {
      item.style.transition = 'none';
    });
  }

  // ✅ 7. SMOOTH SCROLL FOR BANNER CTA
  const bannerCTAs = carousel.querySelectorAll('.carousel-caption .btn[href^="#"]');
  bannerCTAs.forEach(btn => {
    btn.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href && href !== '#') {
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });
  });

  // ✅ 8. FALLBACK: Force load all images after 3s
  setTimeout(() => {
    const unloadedImages = carousel.querySelectorAll('.banner-img:not(.loaded)');
    unloadedImages.forEach(img => {
      img.classList.add('loaded');
      const parent = img.closest('.carousel-item');
      if (parent) parent.classList.remove('loading');
    });
  }, 3000);

  // ✅ 9. ANALYTICS: Track banner views (if GA4/GTM exists)
  if (typeof gtag !== 'undefined') {
    carousel.addEventListener('slid.bs.carousel', function(e) {
      const activeSlide = carousel.querySelector('.carousel-item.active');
      const bannerTitle = activeSlide?.querySelector('h1, h2')?.textContent;
      
      gtag('event', 'banner_view', {
        'event_category': 'Banner',
        'event_label': bannerTitle || `Slide ${e.to + 1}`,
        'value': e.to + 1
      });
    });
  }

  // ✅ 10. PRECONNECT TO CDN (if using Cloudinary/ImgIX)
  const firstBanner = carousel.querySelector('.banner-img');
  if (firstBanner) {
    const src = firstBanner.getAttribute('src') || '';
    if (src.includes('cloudinary.com') || src.includes('imgix.net')) {
      const preconnect = document.createElement('link');
      preconnect.rel = 'preconnect';
      preconnect.href = src.includes('cloudinary') 
        ? 'https://res.cloudinary.com'
        : 'https://assets.imgix.net';
      preconnect.crossOrigin = 'anonymous';
      document.head.appendChild(preconnect);
    }
  }
});

// ==================== RESPONSIVE IMAGE SOURCE HANDLER ====================
// Force browser to re-evaluate <picture> on resize (debounced)
let resizeTimer;
window.addEventListener('resize', function() {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(function() {
    const carousel = document.getElementById('bannerCarousel');
    if (!carousel) return;
    
    const pictures = carousel.querySelectorAll('picture');
    pictures.forEach(picture => {
      const img = picture.querySelector('img');
      if (img) {
        // Force browser to re-check <source> media queries
        img.src = img.src; // Trigger re-evaluation
      }
    });
  }, 250);
});