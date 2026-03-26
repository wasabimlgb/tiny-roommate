import { emitTo, listen } from '@tauri-apps/api/event';
import { getCurrentWindow } from '@tauri-apps/api/window';

const STAGE_PAD = 8;
const HIDE_ANIMATION_MS = 160;

const appWindow = getCurrentWindow();
const bubbleEl = document.getElementById('bubble');
const bubbleTextEl = document.getElementById('bubble-text');
const bubbleArrowEl = document.getElementById('bubble-arrow');
const reactionsEl = document.getElementById('bubble-reactions');
const replyBtn = document.getElementById('bubble-reply');

let hideTimer = null;
let activeId = null;

replyBtn.addEventListener('click', function() {
  emitTo('main', 'bubble:reply', { id: activeId }).catch(function() {});
  hideBubble();
});

function clearArrowStyles() {
  bubbleArrowEl.style.top = '';
  bubbleArrowEl.style.left = '';
  bubbleArrowEl.style.right = '';
  bubbleArrowEl.style.bottom = '';
}

function clearHideTimer() {
  if (hideTimer) {
    clearTimeout(hideTimer);
    hideTimer = null;
  }
}

async function hideBubble(options = {}) {
  clearHideTimer();
  bubbleEl.classList.remove('show');
  await emitTo('main', 'bubble:hidden', { id: activeId });
  if (!options.skipWindowHide) {
    setTimeout(function() {
      appWindow.hide().catch(function() {});
    }, HIDE_ANIMATION_MS);
  }
}

function renderBubble(payload) {
  activeId = payload.id;
  bubbleEl.style.maxWidth = (payload.maxWidth || 280) + 'px';

  // Render quote (user's message) + pet's response
  bubbleTextEl.innerHTML = '';
  if (payload.quote) {
    var quoteEl = document.createElement('div');
    quoteEl.className = 'bubble-quote';
    quoteEl.textContent = payload.quote;
    bubbleTextEl.appendChild(quoteEl);
  }
  bubbleTextEl.appendChild(document.createTextNode(payload.text || ''));

  reactionsEl.innerHTML = '';

  (payload.reactions || []).forEach(function(reaction) {
    const button = document.createElement('button');
    button.textContent = reaction;
    button.addEventListener('click', function() {
      emitTo('main', 'bubble:reaction', { id: activeId, reaction: reaction }).catch(function() {});
      hideBubble();
    });
    reactionsEl.appendChild(button);
  });
}

function applyPlacement(payload) {
  clearArrowStyles();
  bubbleEl.style.left = STAGE_PAD + 'px';
  bubbleEl.style.top = STAGE_PAD + 'px';

  if (payload.arrowSide === 'bottom') {
    bubbleArrowEl.style.bottom = '-5px';
    bubbleArrowEl.style.left = Math.round(payload.arrowOffset - 5) + 'px';
  } else if (payload.arrowSide === 'left') {
    bubbleArrowEl.style.left = '-5px';
    bubbleArrowEl.style.top = Math.round(payload.arrowOffset - 5) + 'px';
  } else {
    bubbleArrowEl.style.right = '-5px';
    bubbleArrowEl.style.top = Math.round(payload.arrowOffset - 5) + 'px';
  }
}

listen('bubble:prepare', async function(event) {
  clearHideTimer();
  bubbleEl.classList.remove('show');
  bubbleEl.style.visibility = 'hidden';
  renderBubble(event.payload);
  await new Promise(function(resolve) { requestAnimationFrame(resolve); });

  await emitTo('main', 'bubble:measured', {
    id: event.payload.id,
    bubbleWidth: Math.ceil(bubbleEl.offsetWidth),
    bubbleHeight: Math.ceil(bubbleEl.offsetHeight),
    windowWidth: Math.ceil(bubbleEl.offsetWidth + STAGE_PAD * 2),
    windowHeight: Math.ceil(bubbleEl.offsetHeight + STAGE_PAD * 2),
  });
});

listen('bubble:display', async function(event) {
  clearHideTimer();
  renderBubble(event.payload);
  applyPlacement(event.payload);

  await appWindow.setSize({
    type: 'Physical',
    width: event.payload.windowWidth,
    height: event.payload.windowHeight,
  });
  await appWindow.setPosition({
    type: 'Physical',
    x: event.payload.x,
    y: event.payload.y,
  });

  bubbleEl.style.visibility = 'visible';
  await appWindow.show();
  bubbleEl.classList.add('show');

  hideTimer = setTimeout(function() {
    hideBubble();
  }, event.payload.duration || 4000);
});

listen('bubble:hide', function() {
  hideBubble();
});

appWindow.hide().catch(function() {});
emitTo('main', 'bubble:ready', { label: 'bubble' }).catch(function() {});
