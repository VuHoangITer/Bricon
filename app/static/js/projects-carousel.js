// ==================== FEATURED PROJECTS CAROUSEL WITH MOUSE DRAG ====================
(function () {
  "use strict";

  const carousel = document.getElementById("projectsCarousel");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  const dotsContainer = document.getElementById("carouselDots");

  // Exit if carousel doesn't exist
  if (!carousel || !dotsContainer) {
    console.warn("Featured Projects Carousel: Required elements not found");
    return;
  }

  const slides = carousel.querySelectorAll(".project-slide");
  const totalSlides = slides.length;

  if (totalSlides === 0) {
    console.warn("Featured Projects Carousel: No slides found");
    return;
  }

  let currentIndex = 0;
  let autoSlideInterval = null;

  // Mouse drag variables
  let isDragging = false;
  let startPos = 0;
  let currentTranslate = 0;
  let prevTranslate = 0;
  let animationID = 0;

  // Configuration
  const config = {
    autoSlideDelay: 5000,
    transitionDuration: 600,
    dragThreshold: 50,
  };

  // ==================== INITIALIZATION ====================
  function init() {
    createDots();
    setupEventListeners();
    updateCarousel(false);
    startAutoSlide();

    // Pause when tab is hidden
    document.addEventListener("visibilitychange", handleVisibilityChange);

    // Handle window resize
    window.addEventListener("resize", debounce(handleResize, 250));

    console.log(
      `Featured Projects Carousel: Initialized with ${totalSlides} slides`
    );
  }

  // ==================== DOTS CREATION ====================
  function createDots() {
    dotsContainer.innerHTML = ""; // Clear existing dots

    slides.forEach((_, index) => {
      const dot = document.createElement("div");
      dot.className = "dot";
      if (index === 0) dot.classList.add("active");
      dot.setAttribute("aria-label", `Go to slide ${index + 1}`);
      dot.setAttribute("data-index", index);
      dot.addEventListener("click", () => goToSlide(index));
      dotsContainer.appendChild(dot);
    });

    console.log(`Created ${slides.length} dots`);
  }

  // ==================== CAROUSEL UPDATES ====================
  function updateCarousel(smooth = true) {
    // Set transition
    if (smooth) {
      carousel.style.transition = `transform ${config.transitionDuration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
    } else {
      carousel.style.transition = "none";
    }

    // Calculate and apply transform
    const offset = -currentIndex * 100;
    carousel.style.transform = `translateX(${offset}%)`;

    // Update dots
    const currentDots = dotsContainer.querySelectorAll(".dot");
    currentDots.forEach((dot, index) => {
      dot.classList.toggle("active", index === currentIndex);
    });

    // Update ARIA attributes
    slides.forEach((slide, index) => {
      slide.setAttribute("aria-hidden", index !== currentIndex);
    });
  }

  function goToSlide(index) {
    if (index < 0 || index >= totalSlides) return;
    currentIndex = index;
    updateCarousel();
    resetAutoSlide();
  }

  function nextSlide() {
    currentIndex = (currentIndex + 1) % totalSlides;
    updateCarousel();
  }

  function prevSlide() {
    currentIndex = (currentIndex - 1 + totalSlides) % totalSlides;
    updateCarousel();
  }

  // ==================== AUTO SLIDE ====================
  function startAutoSlide() {
    stopAutoSlide(); // Clear any existing interval
    autoSlideInterval = setInterval(nextSlide, config.autoSlideDelay);
  }

  function stopAutoSlide() {
    if (autoSlideInterval) {
      clearInterval(autoSlideInterval);
      autoSlideInterval = null;
    }
  }

  function resetAutoSlide() {
    stopAutoSlide();
    startAutoSlide();
  }

  // ==================== DRAG FUNCTIONALITY ====================
  function getPositionX(event) {
    return event.type.includes("mouse")
      ? event.pageX
      : event.touches[0].clientX;
  }

  function dragStart(event) {
    // Ignore if clicking on buttons or links
    if (event.target.closest("a, button")) {
      return;
    }

    isDragging = true;
    startPos = getPositionX(event);
    animationID = requestAnimationFrame(animation);
    stopAutoSlide();

    carousel.style.cursor = "grabbing";
    carousel.classList.add("dragging");
  }

  function dragMove(event) {
    if (!isDragging) return;

    const currentPosition = getPositionX(event);
    const diff = currentPosition - startPos;
    currentTranslate = prevTranslate + diff;
  }

  function dragEnd() {
    if (!isDragging) return;

    isDragging = false;
    cancelAnimationFrame(animationID);

    carousel.style.cursor = "grab";
    carousel.classList.remove("dragging");

    const movedBy = currentTranslate - prevTranslate;

    // Determine if we should change slide
    if (Math.abs(movedBy) > config.dragThreshold) {
      if (movedBy < 0) {
        nextSlide();
      } else {
        prevSlide();
      }
    } else {
      updateCarousel();
    }

    prevTranslate = -currentIndex * carousel.offsetWidth;
    currentTranslate = prevTranslate;
    startAutoSlide();
  }

  function animation() {
    if (!isDragging) return;

    const slideWidth = carousel.offsetWidth;
    const maxTranslate = 0;
    const minTranslate = -(totalSlides - 1) * slideWidth;

    // Limit dragging beyond boundaries
    if (currentTranslate > maxTranslate) {
      currentTranslate = maxTranslate + (currentTranslate - maxTranslate) * 0.3; // Rubber band effect
    }
    if (currentTranslate < minTranslate) {
      currentTranslate = minTranslate + (currentTranslate - minTranslate) * 0.3;
    }

    const percentageTranslate = (currentTranslate / slideWidth) * 100;

    carousel.style.transition = "none";
    carousel.style.transform = `translateX(${percentageTranslate}%)`;

    animationID = requestAnimationFrame(animation);
  }

  // ==================== EVENT LISTENERS ====================
  function setupEventListeners() {
    // Mouse events
    carousel.addEventListener("mousedown", dragStart);
    carousel.addEventListener("mousemove", dragMove);
    carousel.addEventListener("mouseup", dragEnd);
    carousel.addEventListener("mouseleave", () => {
      if (isDragging) dragEnd();
    });

    // Touch events
    carousel.addEventListener("touchstart", dragStart, { passive: true });
    carousel.addEventListener("touchmove", dragMove, { passive: true });
    carousel.addEventListener("touchend", dragEnd);

    // Prevent context menu and text selection
    carousel.addEventListener("contextmenu", (e) => e.preventDefault());
    carousel.addEventListener("dragstart", (e) => e.preventDefault());

    // Set cursor style
    carousel.style.cursor = "grab";

    // Hover to pause auto-slide
    carousel.addEventListener("mouseenter", stopAutoSlide);
    carousel.addEventListener("mouseleave", () => {
      if (!isDragging) startAutoSlide();
    });

    // Keyboard navigation
    document.addEventListener("keydown", handleKeyboard);

    // Button events (if visible)
    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        nextSlide();
        resetAutoSlide();
      });
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", () => {
        prevSlide();
        resetAutoSlide();
      });
    }
  }

  // ==================== UTILITY FUNCTIONS ====================
  function handleKeyboard(e) {
    // Only handle if carousel is in viewport
    const rect = carousel.getBoundingClientRect();
    const isInView = rect.top < window.innerHeight && rect.bottom >= 0;

    if (!isInView) return;

    if (e.key === "ArrowLeft") {
      prevSlide();
      resetAutoSlide();
    } else if (e.key === "ArrowRight") {
      nextSlide();
      resetAutoSlide();
    }
  }

  function handleVisibilityChange() {
    if (document.hidden) {
      stopAutoSlide();
    } else {
      startAutoSlide();
    }
  }

  function handleResize() {
    prevTranslate = -currentIndex * carousel.offsetWidth;
    currentTranslate = prevTranslate;
    updateCarousel(false);
  }

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

  // ==================== CLEANUP ====================
  function destroy() {
    stopAutoSlide();
    document.removeEventListener("visibilitychange", handleVisibilityChange);
    window.removeEventListener("resize", handleResize);
    document.removeEventListener("keydown", handleKeyboard);
    console.log("Featured Projects Carousel: Destroyed");
  }

  // Expose destroy method globally if needed
  window.destroyProjectsCarousel = destroy;

  // Initialize carousel
  init();
})();
