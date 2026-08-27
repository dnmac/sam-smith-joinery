/* Sam Smith Joinery — progressive enhancement only. Everything below is optional:
   with JS off the nav is still a plain list and the form still submits to its action. */
(function () {
  'use strict';

  /* --- mobile navigation ------------------------------------------------ */

  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }

  /* --- gallery filtering ------------------------------------------------ */

  var filters = document.querySelector('.gallery-filters');
  var gallery = document.querySelector('.gallery');

  if (filters && gallery) {
    filters.addEventListener('click', function (event) {
      var button = event.target.closest('button[data-filter]');
      if (!button) return;

      var wanted = button.getAttribute('data-filter');
      Array.prototype.forEach.call(filters.querySelectorAll('button'), function (other) {
        other.setAttribute('aria-pressed', String(other === button));
      });
      Array.prototype.forEach.call(gallery.querySelectorAll('figure'), function (figure) {
        var category = figure.getAttribute('data-category') || '';
        figure.hidden = wanted !== 'all' && category !== wanted;
      });
    });
  }

  /* --- booking form ----------------------------------------------------- */

  var form = document.getElementById('booking-form');
  if (!form) return;

  var status = document.getElementById('form-status');

  // Nobody books yesterday. Stops the obvious data-entry mistake at source.
  var dateField = form.querySelector('input[type="date"]');
  if (dateField && !dateField.min) {
    dateField.min = new Date().toISOString().split('T')[0];
  }

  var MESSAGES = {
    valueMissing: 'Please fill this in so Sam can come back to you.',
    typeMismatch: 'That does not look quite right — please check it.',
    tooShort: 'Please give a little more detail.',
    patternMismatch: 'Please use a valid UK phone number.'
  };

  function messageFor(field) {
    var v = field.validity;
    if (v.valueMissing) return MESSAGES.valueMissing;
    if (v.typeMismatch) return MESSAGES.typeMismatch;
    if (v.tooShort) return MESSAGES.tooShort;
    if (v.patternMismatch) return MESSAGES.patternMismatch;
    return field.validationMessage;
  }

  function errorSlot(field) {
    return document.getElementById(field.id + '-error');
  }

  function showError(field, message) {
    var slot = errorSlot(field);
    field.setAttribute('aria-invalid', 'true');
    if (slot) slot.textContent = message;
  }

  function clearError(field) {
    var slot = errorSlot(field);
    field.removeAttribute('aria-invalid');
    if (slot) slot.textContent = '';
  }

  function validate(field) {
    if (field.name === 'company-website') return true;
    if (field.checkValidity()) {
      clearError(field);
      return true;
    }
    showError(field, messageFor(field));
    return false;
  }

  var controls = Array.prototype.slice.call(
    form.querySelectorAll('input, select, textarea')
  );

  controls.forEach(function (field) {
    field.addEventListener('blur', function () {
      if (field.value !== '' || field.hasAttribute('required')) validate(field);
    });
    field.addEventListener('input', function () {
      if (field.getAttribute('aria-invalid') === 'true') validate(field);
    });
  });

  function announce(message, kind) {
    if (!status) return;
    status.hidden = false;
    status.textContent = message;
    status.className = 'form-status is-' + kind;
  }

  form.addEventListener('submit', function (event) {
    var honeypot = form.querySelector('input[name="company-website"]');
    if (honeypot && honeypot.value !== '') {
      event.preventDefault();
      return;
    }

    var firstInvalid = null;
    controls.forEach(function (field) {
      if (!validate(field) && !firstInvalid) firstInvalid = field;
    });

    if (firstInvalid) {
      event.preventDefault();
      announce('Please check the highlighted fields and try again.', 'error');
      firstInvalid.focus();
      return;
    }

    // No back end is wired up yet — see README. Confirm in-page instead of
    // posting to a placeholder endpoint that would 404 in front of a customer.
    if (form.getAttribute('data-demo') === 'true') {
      event.preventDefault();
      announce(
        'Thanks! Your enquiry has been recorded. Sam aims to reply within one working day.',
        'success'
      );
      form.reset();
      if (status) status.focus();
    }
  });
})();
