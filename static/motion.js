"use strict";
(() => {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  const sections = [...document.querySelectorAll(".reveal[data-reveal]")];
  const animations = new Set();
  let observer;
  const allowed = () => !reduced.matches && !document.body.classList.contains("presentation-mode");
  function cancelAnimations() {
    animations.forEach((animation) => animation.cancel());
    animations.clear();
  }
  function revealAll() {
    observer?.disconnect();
    sections.forEach((section) => section.classList.add("is-revealed"));
    document.documentElement.dataset.motionReady = "false";
  }
  if (allowed() && "IntersectionObserver" in window) {
    observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-revealed");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.05 });
    sections.forEach((section) => observer.observe(section));
    document.documentElement.dataset.motionReady = "true";
  } else revealAll();
  document.addEventListener("pagamentos:updated", (event) => {
    if (!event.detail.full || !allowed()) return;
    cancelAnimations();
    // Numbers are set to their final values before this subtle transition.
    document.querySelectorAll(".kpi > strong, .chart-insight, #leitura-recorte").forEach((element, index) => {
      if (typeof element.animate !== "function") return;
      const animation = element.animate([
        { opacity: 0.45, transform: "translateY(6px)" },
        { opacity: 1, transform: "translateY(0)" },
      ], { duration: 320, delay: Math.min(index * 25, 120), easing: "cubic-bezier(.2,.7,.3,1)" });
      animations.add(animation);
      animation.onfinish = animation.oncancel = () => animations.delete(animation);
    });
  });
  document.addEventListener("pagamentos:loading", (event) => { if (event.detail.active) cancelAnimations(); });
  document.addEventListener("pagamentos:presentation", (event) => {
    cancelAnimations();
    if (event.detail.active) revealAll();
  });
  reduced.addEventListener("change", () => { cancelAnimations(); if (reduced.matches) revealAll(); });
})();
