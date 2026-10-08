/* 佐世保 終活相談窓口: Google Analytics 4 event tracking.
 * Configure the GA4 Measurement ID after creating this site's own GA4 web stream.
 * Never put customer names, phone numbers, emails, or survey answers in analytics events.
 */
(function () {
  "use strict";

  // TODO: Set this site's GA4 measurement ID (example: G-XXXXXXXXXX).
  // Leave empty until its dedicated data stream has been created.
  const GA4_MEASUREMENT_ID = "";
  const enabled = /^G-[A-Z0-9]+$/.test(GA4_MEASUREMENT_ID);

  if (enabled) {
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", GA4_MEASUREMENT_ID);
    const tag = document.createElement("script");
    tag.async = true;
    tag.src = "https://www.googletagmanager.com/gtag/js?id=" +
      encodeURIComponent(GA4_MEASUREMENT_ID);
    document.head.appendChild(tag);
  }

  function track(name, params) {
    if (enabled && typeof window.gtag === "function") {
      window.gtag("event", name, params || {});
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Measure interest in the 60-second questionnaire on all pages.
    document.querySelectorAll('a[href="#check"],a[href="./#check"]').forEach(function (link) {
      link.addEventListener("click", function () {
        track("check_cta_click", { source_page: location.pathname.endsWith(".html") ?
          location.pathname.split("/").pop() : "home" });
      });
    });

    const quiz = document.getElementById("check");
    if (!quiz) return;

    let quizStarted = false;
    let quizCompleted = false;
    quiz.addEventListener("click", function (e) {
      if (e.target.closest(".q-choice") && !quizStarted) {
        quizStarted = true;
        track("quiz_start", { quiz_id: "sasebo_hakajimai_7q" });
      }
    });

    const next = document.getElementById("nextBtn");
    const result = document.getElementById("resultPane");
    if (next && result) {
      next.addEventListener("click", function () {
        if (!quizCompleted && result.style.display === "block") {
          quizCompleted = true;
          track("quiz_complete", { quiz_id: "sasebo_hakajimai_7q" });
        }
      });
    }

    const leadForm = document.getElementById("leadForm");
    const submitFrame = document.getElementById("submitFrame");
    if (!leadForm) return;

    let awaitingFrame = false;
    let responseCounted = false;
    leadForm.addEventListener("submit", function () {
      // Fired only after native form validation succeeds, before POST is sent.
      awaitingFrame = true;
      responseCounted = false;
      track("lead_form_submit_attempt", { form_id: "leadForm" });
    });

    if (submitFrame) {
      submitFrame.addEventListener("load", function () {
        // An iframe load is an indication of a POST response, NOT a verified
        // Apps Script / spreadsheet success acknowledgment.
        if (!awaitingFrame || responseCounted) return;
        awaitingFrame = false;
        responseCounted = true;
        track("lead_form_response_loaded", { form_id: "leadForm" });
        // Do not log generate_lead here without verified server-side success.
      });
    }
  });
})();
