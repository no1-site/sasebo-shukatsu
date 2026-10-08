/* 佐世保 終活相談窓口: Google Analytics 4 event tracking.
 * Configure the GA4 Measurement ID after creating this site's own GA4 web stream.
 * Never put customer names, phone numbers, emails, or survey answers in analytics events.
 */
(function () {
  "use strict";

  // Shared GA4 measurement ID for this site.
  // The homepage already loads the Google tag inline; do not configure it twice.
  const GA4_MEASUREMENT_ID = "G-VN5SKDQH5H";
  const enabled = /^G-[A-Z0-9]+$/.test(GA4_MEASUREMENT_ID);

  if (enabled && typeof window.gtag !== "function") {
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

  // Read identifiers from GA4 without reading or transmitting personal details.
  // gtag callbacks may arrive asynchronously; do not delay the inquiry form.
  let gaClientId = "";
  let gaSessionId = "";
  function loadGaIdentifiers() {
    if (!enabled || typeof window.gtag !== "function") return;
    try {
      window.gtag("get", GA4_MEASUREMENT_ID, "client_id", function (value) {
        const id = String(value || "").trim();
        if (/^\d+\.\d+$/.test(id)) gaClientId = id;
      });
      window.gtag("get", GA4_MEASUREMENT_ID, "session_id", function (value) {
        const id = String(value || "").trim();
        if (/^\d+$/.test(id)) gaSessionId = id;
      });
    } catch (error) {
      // Analytics must never stop the inquiry form.
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    loadGaIdentifiers();
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
      // Homepage's earlier submit listener has already serialized questionnaire
      // answers into the payloadField. Add GA4-only identifiers to that JSON.
      const payloadField = document.getElementById("payloadField");
      if (payloadField && payloadField.value) {
        try {
          const payload = JSON.parse(payloadField.value);
          if (gaClientId) payload.ga_client_id = gaClientId;
          if (gaSessionId) payload.ga_session_id = gaSessionId;
          payloadField.value = JSON.stringify(payload);
        } catch (error) {
          // Leave the original payload unchanged if it isn't valid JSON.
        }
      }

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
