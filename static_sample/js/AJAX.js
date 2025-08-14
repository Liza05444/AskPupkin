function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.voting-buttons').forEach(container => {
        const activeBtn = container.querySelector('.btn-vote.active');
        if (activeBtn) {
            const value = parseInt(activeBtn.dataset.value);
            updateVoteButtons(container, value);
        }
    });
});

function updateVoteButtons(container, userVote) {
    container.querySelectorAll('.btn-vote').forEach(btn => {
        btn.classList.remove('active');
    });

    if (userVote === 1) {
        container.querySelector('.btn-like').classList.add('active');
    } else if (userVote === -1) {
        container.querySelector('.btn-dislike').classList.add('active');
    }
}

document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.btn-vote');
    if (!btn) return;
    e.preventDefault();
    const container = btn.closest('.voting-buttons');
    const type = btn.dataset.questionId ? 'question' : 'answer';
    const id = btn.dataset.questionId || btn.dataset.answerId;
    const value = parseInt(btn.dataset.value);
    const csrftoken = getCookie('csrftoken');
    try {
        const formData = new FormData();
        formData.append(`${type}_id`, id);
        formData.append('value', value);
        formData.append('csrfmiddlewaretoken', csrftoken);
        const url = type === 'question' ? '/question/like/' : '/answer/like/';
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            throw new Error(`Error! status: ${response.status}`);
        }
        const data = await response.json();
        container.querySelector('.rating-value').textContent = data.rating;
        updateVoteButtons(container, data.user_vote);
    } catch (error) {
        console.error('Error:', error);
        alert('Error occurred while processing your vote. Please try again.');
    }
});

document.addEventListener('change', async function(e) {
    const checkbox = e.target.closest('.mark-correct-checkbox');
    if (!checkbox) return;
    const answerId = checkbox.dataset.answerId;
    const isChecked = checkbox.checked;
    const answerCard = checkbox.closest('.answer-card');
    const badge = answerCard?.querySelector('.correct-badge');
    const csrftoken = getCookie('csrftoken');
    checkbox.disabled = true;
    try {
        const response = await fetch('/answer/mark-correct/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: `answer_id=${answerId}&is_correct=${isChecked}`
        });
        if (!response.ok) {
            throw new Error(`Error! status: ${response.status}`);
        }
        const data = await response.json();
        if (badge) {
            badge.style.display = data.is_correct ? 'block' : 'none';
        }
    } catch (error) {
        console.error('Error:', error);
        checkbox.checked = !isChecked;
    } finally {
        checkbox.disabled = false;
    }
});