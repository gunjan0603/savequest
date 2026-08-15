document.addEventListener('DOMContentLoaded', () => {
  const dateInput = document.getElementById('saving-date');
  if (dateInput) dateInput.value = new Date().toISOString().slice(0, 10);

  const form = document.getElementById('savings-form');
  if (!form) return;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const amount = Number(document.getElementById('saving-amount').value);
    const dateLogged = document.getElementById('saving-date').value;
    const note = document.getElementById('saving-note').value;
    const feedback = document.getElementById('save-feedback');
    const goalId = window.location.pathname.split('/')[2];
    if (!amount || amount <= 0 || !dateLogged) {
      feedback.textContent = 'Please enter a valid amount and date.';
      feedback.className = 'save-feedback error';
      return;
    }
    feedback.textContent = 'Saving your progress…';
    feedback.className = 'save-feedback';
    try {
      const response = await fetch(`/api/goals/${goalId}/savings`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({amount, date_logged: dateLogged, note})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not log savings.');
      document.getElementById('saved-amount').textContent = Math.round(data.goal.saved_amount).toLocaleString('en-IN');
      document.getElementById('progress-percent').textContent = `${data.goal.progress_percentage}% complete`;
      document.getElementById('progress-bar').style.width = `${data.goal.progress_percentage}%`;
      const item = document.createElement('div');
      item.className = 'history-item';
      item.innerHTML = `<div><strong>₹${Number(data.entry.amount).toLocaleString('en-IN')}</strong><span>${data.entry.date_logged}</span></div><b>+${data.entry.points_earned} pts${data.entry.is_streak_bonus ? ' 🔥' : ''}</b>`;
      const history = document.getElementById('history-list');
      const empty = history.querySelector('.small-empty');
      if (empty) empty.remove();
      history.prepend(item);
      feedback.textContent = `✨ +${data.entry.points_earned} points! ${data.entry.is_streak_bonus ? 'Consistency bonus unlocked.' : 'Nice saving move.'}`;
      feedback.className = 'save-feedback success';
      form.reset();
      dateInput.value = new Date().toISOString().slice(0, 10);
      if (data.goal.is_completed) setTimeout(() => window.location.reload(), 1200);
    } catch (error) {
      feedback.textContent = error.message;
      feedback.className = 'save-feedback error';
    }
  });
});
