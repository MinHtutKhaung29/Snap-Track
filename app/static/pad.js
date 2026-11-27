(function () {
  var pad = document.querySelector('[data-pad]');
  if (!pad) {
    return;
  }
  var form = pad.closest('form');
  var input = form ? form.querySelector('input[name="amount"]') : null;
  if (!form || !input) {
    return;
  }
  pad.hidden = false;
  document.body.classList.add('has-pad');
  input.setAttribute('inputmode', 'none');

  function tidy() {
    var digits = input.value.replace(/[^0-9]/g, '').slice(0, 9);
    if (digits !== input.value) {
      input.value = digits;
    }
  }

  pad.addEventListener('click', function (event) {
    var key = event.target.closest('[data-key]');
    if (!key) {
      return;
    }
    event.preventDefault();
    var value = key.getAttribute('data-key');
    if (value === 'del') {
      input.value = input.value.slice(0, -1);
    } else if (input.value.replace(/^0+(?=\d)/, '').length < 9) {
      input.value = input.value === '0' ? value : input.value + value;
    }
    tidy();
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });

  input.addEventListener('input', tidy);

  form.addEventListener('submit', function () {
    tidy();
    var save = pad.querySelector('.pad-save');
    if (save) {
      save.disabled = true;
      save.textContent = '保存中…';
    }
  });
})();
