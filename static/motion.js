"use strict";
(() => {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  const sections = [...document.querySelectorAll(".reveal[data-reveal]")];
  const animations = new Set();
  const ease = "cubic-bezier(.16,1,.3,1)";
  let observer;
  let progressAnimation;
  let progressFinish;
  let presentationFrame;
  let loading = false;
  const allowed = () => !reduced.matches && !document.hidden;
  const activeScreen = () => document.querySelector(".dashboard-screen:not([hidden])");
  const inViewport = (element) => {
    if (element.closest?.("[hidden], .is-loading, .is-unavailable")) return false;
    const bounds = element.getBoundingClientRect();
    return bounds.width > 0 && bounds.height > 0 && bounds.bottom > 0 && bounds.top < window.innerHeight;
  };

  function play(element, keyframes, options = {}, cleanup) {
    if (!element || !allowed() || typeof element.animate !== "function") {
      cleanup?.();
      return null;
    }
    const animation = element.animate(keyframes, { duration: 650, easing: ease, fill: "both", ...options });
    let finished = false;
    const handle = { cancel: finish };
    function finish() {
      if (finished) return;
      finished = true;
      animations.delete(handle);
      animation.cancel();
      cleanup?.();
    }
    animations.add(handle);
    animation.onfinish = animation.oncancel = finish;
    return handle;
  }

  function cancelAnimations() {
    [...animations].forEach((animation) => animation.cancel());
    if (presentationFrame) cancelAnimationFrame(presentationFrame);
    presentationFrame = null;
  }

  function releaseBars(section) {
    section.querySelectorAll(".rank-fill, .month-bar").forEach((bar) => { bar.style.animationPlayState = "running"; });
  }

  function reveal(section, delay = 0) {
    section.style.setProperty("--reveal-delay", `${delay}ms`);
    section.classList.add("is-revealed");
    releaseBars(section);
    observer?.unobserve(section);
  }

  function revealAll() {
    observer?.disconnect();
    sections.forEach((section) => reveal(section));
    document.documentElement.dataset.motionReady = "false";
  }

  function revealScreen(screen) {
    if (!screen) return;
    if (screen.matches?.(".reveal[data-reveal]")) reveal(screen);
    screen.querySelectorAll(".reveal[data-reveal]").forEach((section) => reveal(section));
  }

  if (allowed() && "IntersectionObserver" in window) {
    document.documentElement.dataset.motionReady = "true";
    observer = new IntersectionObserver((entries) => {
      entries.filter((entry) => entry.isIntersecting)
        .sort((a, b) => sections.indexOf(a.target) - sections.indexOf(b.target))
        .forEach((entry, index) => reveal(entry.target, Math.min(index * 75, 300)));
    }, { threshold: 0.06 });
    sections.forEach((section) => observer.observe(section));
    for (const [selector, transform] of [[".sidebar", "translateX(-18px)"], [".topbar", "translateY(-10px)"]]) {
      const element = document.querySelector(selector);
      if (element && inViewport(element)) play(element, [{ opacity: 0.65, transform }, { opacity: 1, transform: "translate(0,0)" }], { duration: 800 });
    }
  } else revealAll();

  // Keyboard navigation never waits for a decorative entrance to finish.
  document.addEventListener("focusin", (event) => {
    const section = event.target.closest?.(".reveal[data-reveal]");
    if (section) reveal(section);
  });

  const progress = document.createElement("div");
  progress.className = "query-progress";
  progress.setAttribute("aria-hidden", "true");
  progress.hidden = true;
  const progressBar = document.createElement("span");
  progressBar.className = "query-progress__bar";
  progress.append(progressBar);
  document.body.append(progress);

  function stopProgressAnimation() {
    progressAnimation?.cancel();
    progressAnimation = null;
    progressFinish?.cancel();
    progressFinish = null;
  }

  function showProgress() {
    stopProgressAnimation();
    progress.hidden = false;
    // This is indeterminate activity, never a fabricated completion percentage.
    if (allowed() && typeof progressBar.animate === "function") {
      progressAnimation = progressBar.animate([
        { transform: "translateX(-105%)", opacity: 0.55 },
        { opacity: 1, offset: 0.45 },
        { transform: "translateX(490%)", opacity: 0.55 },
      ], { duration: 1350, iterations: Infinity, easing: "cubic-bezier(.55,.1,.3,.9)" });
    }
  }

  function hideProgress() {
    stopProgressAnimation();
    if (!allowed()) { progress.hidden = true; return; }
    progressFinish = play(progress, [{ opacity: 1 }, { opacity: 0 }], { duration: 220, easing: "ease-out" }, () => {
      if (!loading) progress.hidden = true;
    });
  }

  function prepareBars() {
    for (const selector of [".rank-fill", ".month-bar"]) {
      document.querySelectorAll(selector).forEach((bar, index) => {
        bar.style.setProperty("--bar-delay", `${Math.min(index * 45, 420)}ms`);
        const section = bar.closest(".reveal[data-reveal]");
        const waiting = allowed() && section && !section.classList.contains("is-revealed");
        bar.style.animationPlayState = waiting ? "paused" : "running";
      });
    }
  }

  function replayBars(container = document) {
    if (!allowed()) return;
    container.querySelectorAll(".rank-fill, .month-bar").forEach((bar) => {
      if (!inViewport(bar) || typeof bar.getAnimations !== "function") return;
      // Rewind the existing CSS timeline, including its staggered delay. No duplicate effects or style overrides.
      bar.getAnimations().forEach((animation) => {
        if (animation.animationName === "rank-enter" || animation.animationName === "bar-enter") {
          animation.currentTime = 0;
          animation.play();
        }
      });
    });
  }

  document.addEventListener("pagamentos:updated", (event) => {
    prepareBars();
    if (!allowed()) return;
    cancelAnimations();
    if (!event.detail.full) {
      const table = document.getElementById("registros-tabela");
      if (table && inViewport(table)) play(table, [{ opacity: 0.5, transform: "translateY(7px)" }, { opacity: 1, transform: "translateY(0)" }], { duration: 420 });
      return;
    }
    // app.js has already written the exact final values; only their presentation moves.
    document.querySelectorAll(".kpi").forEach((card, index) => {
      if (!inViewport(card)) return;
      const value = card.querySelector(":scope > strong");
      play(value, [{ opacity: 0.4, transform: "translateY(16px)" }, { opacity: 1, transform: "translateY(0)" }], { delay: index * 65, duration: 700 });
    });
    document.querySelectorAll(".chart-insight, #leitura-recorte").forEach((element, index) => {
      if (inViewport(element)) play(element, [{ opacity: 0.5, transform: "translateY(10px)" }, { opacity: 1, transform: "translateY(0)" }], { duration: 650, delay: 100 + index * 65 });
    });
  });

  document.addEventListener("pagamentos:loading", (event) => {
    loading = event.detail.active;
    if (loading) {
      cancelAnimations();
      showProgress();
    } else hideProgress();
  });

  document.addEventListener("pagamentos:screen", () => {
    cancelAnimations();
    const screen = activeScreen();
    if (!screen) return;
    revealScreen(screen);
    if (!allowed() || !inViewport(screen)) return;
    play(screen, [{ opacity: 0.35, transform: "translateY(12px)" }, { opacity: 1, transform: "translateY(0)" }], { duration: 420 });
    replayBars(screen);
  });

  document.addEventListener("pagamentos:presentation", (event) => {
    cancelAnimations();
    const screen = activeScreen() || document.querySelector("main");
    revealScreen(screen);
    if (!allowed()) return;
    presentationFrame = requestAnimationFrame(() => {
      presentationFrame = null;
      if (!screen || !inViewport(screen)) return;
      if (event.detail.active) replayBars(screen);
      play(screen, [{ opacity: 0.62, transform: "translateY(12px)" }, { opacity: 1, transform: "translateY(0)" }], { duration: 480 });
    });
  });

  function adaptMotion() {
    cancelAnimations();
    if (!allowed()) revealAll();
    if (loading) showProgress();
    else { stopProgressAnimation(); progress.hidden = true; }
  }
  reduced.addEventListener("change", adaptMotion);
  document.addEventListener("visibilitychange", adaptMotion);
  window.addEventListener("pagehide", () => { cancelAnimations(); stopProgressAnimation(); });
  // The first loading event can precede this deferred script.
  loading = document.body.dataset.loading === "true";
  if (loading) showProgress();
})();
