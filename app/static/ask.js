(function () {
  var THRESHOLD = 96;
  var CLAMP = 140;
  var TAP_SLOP = 8;
  var EASE_OUT = 'cubic-bezier(.23,1,.32,1)';
  var PENDING_HINT = '送信中…';
  var motionQuery = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

  function reduced() {
    return !!(motionQuery && motionQuery.matches);
  }

  function thread() {
    return document.getElementById('thread');
  }

  function composer() {
    return document.querySelector('#chat-form textarea[name=message]');
  }

  function stateOf(card) {
    return card.getAttribute('data-state');
  }

  function cardOf(node) {
    if (!node || !node.closest) return null;
    return node.closest('.swipe');
  }

  function openCard(node) {
    var card = cardOf(node);
    return card && stateOf(card) === 'open' ? card : null;
  }

  function choices(card) {
    var found = card.querySelectorAll('[data-swipe]');
    var list = [];
    for (var i = 0; i < found.length; i++) {
      var direction = found[i].getAttribute('data-swipe');
      if (direction !== 'left' && direction !== 'right') continue;
      if (found[i].tagName !== 'FORM' && found[i].tagName !== 'BUTTON') continue;
      list.push(found[i]);
    }
    return list;
  }

  function choiceFor(card, direction) {
    var list = choices(card);
    for (var i = 0; i < list.length; i++) {
      if (list[i].getAttribute('data-swipe') === direction) return list[i];
    }
    return null;
  }

  function buttonOf(node) {
    return node.tagName === 'BUTTON' ? node : node.querySelector('button');
  }

  function lock(card, on) {
    var list = choices(card);
    for (var i = 0; i < list.length; i++) {
      var button = buttonOf(list[i]);
      if (button) button.disabled = on;
    }
  }

  function hintOf(card) {
    return card.querySelector('[data-hint]');
  }

  function hintText(card, text, isError) {
    var hint = hintOf(card);
    if (!hint) return;
    if (hint.getAttribute('data-plain') === null) hint.setAttribute('data-plain', hint.textContent);
    hint.textContent = text;
    if (isError) hint.classList.add('swipe-hint-err');
    else hint.classList.remove('swipe-hint-err');
  }

  function plainHint(card) {
    var hint = hintOf(card);
    if (!hint) return;
    var plain = hint.getAttribute('data-plain');
    if (plain !== null) hint.textContent = plain;
    hint.classList.remove('swipe-hint-err');
  }

  function paint(card, x) {
    var visual = card.querySelector('[data-stamp="' + (x > 0 ? 'right' : 'left') + '"]');
    var other = card.querySelector('[data-stamp="' + (x > 0 ? 'left' : 'right') + '"]');
    if (visual) {
      var progress = Math.min(1, Math.abs(x) / THRESHOLD);
      visual.style.opacity = String(progress);
      visual.style.transform = reduced() ? 'none' : 'scale(' + (0.9 + 0.1 * progress).toFixed(3) + ')';
    }
    if (other) {
      other.style.opacity = '0';
    }
    if (reduced()) return;
    card.style.transform = 'translateX(' + x + 'px) rotate(' + (x / CLAMP * 5).toFixed(2) + 'deg)';
  }

  function reset(card) {
    card.style.transition = '';
    card.style.transform = '';
    card.style.opacity = '';
    var stamps = card.querySelectorAll('[data-stamp]');
    for (var index = 0; index < stamps.length; index += 1) {
      stamps[index].style.opacity = '';
      stamps[index].style.transform = '';
    }
  }

  function center(card, animate) {
    if (!animate || reduced()) {
      reset(card);
      return;
    }
    card.style.transition = 'transform 200ms ' + EASE_OUT + ', opacity 200ms ' + EASE_OUT;
    card.style.transform = '';
    card.style.opacity = '';
  }

  function flyOut(card, direction, animate) {
    if (!animate || reduced()) {
      card.style.transition = 'none';
      return;
    }
    var span = card.offsetWidth || 320;
    var sign = direction === 'right' ? 1 : -1;
    card.style.transition = 'transform 200ms ' + EASE_OUT + ', opacity 200ms ' + EASE_OUT;
    card.style.transform = 'translateX(' + sign * (span + 40) + 'px) rotate(' + sign * 8 + 'deg)';
    card.style.opacity = '0';
  }

  function dedupeLinks() {
    var links = document.querySelectorAll('link[rel="stylesheet"][href="/static/ask.css"]');
    for (var i = 1; i < links.length; i++) links[i].remove();
  }

  function fragment(html) {
    var box = document.createElement('template');
    box.innerHTML = html || '';
    return box.content;
  }

  function focusComposer() {
    var field = composer();
    if (field) field.focus({ preventScroll: true });
  }

  function pending(card) {
    card.setAttribute('data-state', 'pending');
    card.setAttribute('aria-busy', 'true');
    hintText(card, PENDING_HINT, false);
    lock(card, true);
  }

  function reopen(card) {
    card.removeAttribute('aria-busy');
    card.setAttribute('data-state', 'open');
    plainHint(card);
    lock(card, false);
  }

  function fail(card, status) {
    card.removeAttribute('aria-busy');
    card.setAttribute('data-state', 'open');
    reset(card);
    lock(card, false);
    hintText(
      card,
      status === 409 ? 'すでに回答済みです。' : '送信できませんでした。通信を確認してもう一度お試しください。',
      true
    );
  }

  function succeed(card, result) {
    var hadFocus = card.contains(document.activeElement);
    var cardPiece = fragment(result.card_html);
    var fresh = cardPiece.querySelector('.swipe');
    if (fresh) card.replaceWith(fresh);
    var rows = fragment(result.html);
    var region = thread();
    if (region) {
      while (rows.firstChild) {
        var node = rows.firstChild;
        if (node.nodeType === 1) region.appendChild(node);
        else rows.removeChild(node);
      }
    }
    dedupeLinks();
    if (hadFocus || document.activeElement === document.body || !document.activeElement) focusComposer();
  }

  function remote(card, choice) {
    var body = new FormData();
    body.set('csrf_token', card.getAttribute('data-csrf') || '');
    body.set('choice', choice.getAttribute('data-choice') || '');
    fetch(card.getAttribute('data-endpoint'), {
      method: 'POST',
      body: body,
      headers: { Accept: 'application/json' },
      credentials: 'same-origin'
    })
      .then(function (response) {
        return response.json().then(function (payload) {
          return { status: response.status, payload: payload };
        });
      })
      .then(function (answer) {
        if (answer.payload && answer.payload.ok) succeed(card, answer.payload);
        else fail(card, answer.status);
      })
      .catch(function () {
        fail(card, 0);
      });
  }

  function submit(card, form) {
    var settled = false;
    function undo() {
      if (settled) return;
      settled = true;
      reopen(card);
      center(card, true);
    }
    form.addEventListener('submit', function (event) {
      if (event.defaultPrevented) undo();
    });
    form.addEventListener('invalid', undo, true);
    try {
      if (form.requestSubmit) form.requestSubmit();
      else form.submit();
    } catch (error) {
      undo();
    }
  }

  function activate(card, choice, animate) {
    if (stateOf(card) !== 'open') return;
    var direction = choice.getAttribute('data-swipe');
    pending(card);
    if (card.hasAttribute('data-endpoint')) {
      flyOut(card, direction, animate);
      remote(card, choice);
      return;
    }
    center(card, animate);
    if (choice.tagName === 'FORM') {
      submit(card, choice);
      return;
    }
    var button = buttonOf(choice);
    if (button && button.form) {
      submit(card, button.form);
      return;
    }
    reopen(card);
  }

  function release(card, drag) {
    if (!drag.moved) {
      if (drag.choice) activate(card, drag.choice, true);
      else reset(card);
      return;
    }
    if (Math.abs(drag.x) < THRESHOLD) {
      reset(card);
      return;
    }
    var choice = choiceFor(card, drag.x > 0 ? 'right' : 'left');
    if (choice) activate(card, choice, true);
    else reset(card);
  }

  function typing(node) {
    if (!node || !node.tagName) return false;
    var tag = node.tagName;
    return tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA' || node.isContentEditable === true;
  }

  var drag = null;
  var skipClick = false;

  document.addEventListener('pointerdown', function (event) {
    if (event.button) return;
    if (drag) return;
    skipClick = false;
    var card = openCard(event.target);
    if (!card) return;
    drag = {
      card: card,
      id: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      x: 0,
      moved: false,
      captured: false,
      choice: event.target.closest('[data-swipe]')
    };
    card.style.transition = 'none';
  });

  document.addEventListener('pointermove', function (event) {
    if (!drag || event.pointerId !== drag.id) return;
    var dx = event.clientX - drag.startX;
    var dy = event.clientY - drag.startY;
    if (!drag.moved && Math.abs(dx) < TAP_SLOP && Math.abs(dy) < TAP_SLOP) return;
    if (!drag.moved && !drag.horizontal && !drag.vertical) {
      if (Math.abs(dx) < Math.abs(dy) * 1.5) {
        drag.vertical = true;
        return;
      }
      drag.horizontal = true;
    }
    if (drag.vertical) return;
    if (!drag.captured) {
      drag.captured = true;
      try {
        drag.card.setPointerCapture(event.pointerId);
      } catch (error) {}
    }
    drag.moved = true;
    drag.x = Math.max(-CLAMP, Math.min(CLAMP, dx));
    paint(drag.card, drag.x);
  });

  function end(event) {
    if (!drag || event.pointerId !== drag.id) return;
    var current = drag;
    drag = null;
    skipClick = current.moved && !current.vertical;
    if (current.captured) {
      try {
        current.card.releasePointerCapture(event.pointerId);
      } catch (error) {}
    }
    if (current.vertical) {
      reset(current.card);
      return;
    }
    release(current.card, current);
  }

  document.addEventListener('pointerup', end);

  document.addEventListener('pointercancel', function (event) {
    if (!drag || event.pointerId !== drag.id) return;
    var card = drag.card;
    drag = null;
    reset(card);
  });

  document.addEventListener('keydown', function (event) {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    if (typing(event.target)) return;
    var card = openCard(event.target);
    if (!card) return;
    var direction = event.key === 'ArrowRight' ? 'right' : event.key === 'ArrowLeft' ? 'left' : null;
    if (!direction) return;
    var choice = choiceFor(card, direction);
    if (!choice) return;
    event.preventDefault();
    var target = buttonOf(choice);
    if (target) target.focus();
  });

  document.addEventListener('click', function (event) {
    if (skipClick) {
      skipClick = false;
      return;
    }
    var card = cardOf(event.target);
    if (!card) return;
    var choice = event.target.closest('[data-swipe]');
    if (!choice || choice.closest('.swipe') !== card) return;
    event.preventDefault();
    activate(card, choice, event.detail !== 0);
  });

  dedupeLinks();
})();

(function () {
  var thread = document.getElementById('thread');
  if (!thread) return;
  var active = null;

  function promote(card) {
    if (active) return;
    active = {
      card: card,
      parent: card.parentNode,
      next: card.nextSibling,
      focus: document.activeElement
    };
    var veil = document.createElement('div');
    veil.className = 'veil';
    var wrap = document.createElement('div');
    wrap.className = 'modal-wrap';
    document.body.appendChild(veil);
    document.body.appendChild(wrap);
    wrap.appendChild(card);
    active.veil = veil;
    active.wrap = wrap;
    card.classList.remove('is-closed');
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-modal', 'true');
    var close = card.querySelector('[data-modal-close]');
    if (close) close.hidden = false;
    document.body.classList.add('modal-open');
    requestAnimationFrame(function () {
      veil.setAttribute('data-shown', 'true');
    });
    card.focus();
  }

  function close() {
    if (!active) return;
    if (active.card.getAttribute('data-state') === 'pending') return;
    var state = active;
    active = null;
    state.card.classList.remove('is-modal');
    state.card.classList.add('is-closed');
    state.card.removeAttribute('aria-modal');
    state.card.removeAttribute('role');
    var closeButton = state.card.querySelector('[data-modal-close]');
    if (closeButton) closeButton.hidden = true;
    document.body.classList.remove('modal-open');
    state.wrap.remove();
    state.veil.remove();
    if (state.next && state.next.parentNode === state.parent) {
      state.parent.insertBefore(state.card, state.next);
    } else {
      state.parent.appendChild(state.card);
    }
    var target = state.focus && state.focus.focus ? state.focus : state.card;
    target.focus();
  }

  document.addEventListener('click', function (event) {
    if (!active) return;
    if (event.target.closest('[data-modal-close]')) {
      event.preventDefault();
      close();
      return;
    }
    if (event.target.classList && event.target.classList.contains('veil')) {
      close();
    }
  });

  document.addEventListener('keydown', function (event) {
    if (!active || event.key !== 'Escape') return;
    event.preventDefault();
    close();
  });

  thread.addEventListener('click', function (event) {
    if (active) return;
    var card = event.target.closest('.msg.swipe[data-modal]');
    if (!card || event.target.closest('button,form,a')) return;
    promote(card);
  });

  thread.addEventListener('keydown', function (event) {
    if (active) return;
    if (event.key !== 'Enter' && event.key !== ' ') return;
    var card = event.target.closest('.msg.swipe[data-modal]');
    if (!card) return;
    event.preventDefault();
    promote(card);
  });

  function autoPromote() {
    if (active) return;
    var card = thread.querySelector('.msg.swipe[data-modal][data-state="open"]:not(.is-closed)');
    if (card) promote(card);
  }

  new MutationObserver(autoPromote).observe(thread, { childList: true, subtree: true });
  autoPromote();
})();
