// Reviews & Ratings System for Aurum Ghana
class ReviewsSystem {
    constructor() {
        this.selectedRating = 0;
        this.productId = null;
        this.init();
    }

    init() {
        const urlParams = new URLSearchParams(window.location.search);
        this.productId = urlParams.get('id') || urlParams.get('product_id');
        if (this.productId) {
            this.loadProductReviews();
            this.setupReviewForm();
        }
        if (document.getElementById('admin-reviews-section')) {
            this.loadAdminReviews();
        }
    }

    async loadProductReviews() {
        const reviewsContainer = document.getElementById('reviews-list');
        if (!reviewsContainer) return;
        reviewsContainer.innerHTML = '<div class="loading-reviews">Loading reviews...</div>';
        try {
            const data = await window.api.request('/products/' + this.productId + '/reviews');
            if (!data.items || data.items.length === 0) {
                reviewsContainer.innerHTML = '<div class="empty-reviews"><div class="empty-reviews-icon">&#9733;</div><h3 class="empty-reviews-title">No reviews yet</h3><p class="empty-reviews-subtitle">Be the first to share your experience!</p></div>';
                return;
            }
            this.updateReviewSummary(data);
            reviewsContainer.innerHTML = '';
            const self = this;
            data.items.forEach(function(review) {
                reviewsContainer.appendChild(self.createReviewCard(review));
            });
        } catch (error) {
            reviewsContainer.innerHTML = '<div class="loading-reviews">Failed to load reviews.</div>';
        }
    }

    updateReviewSummary(data) {
        const avgRating = data.items.reduce(function(sum, r) { return sum + r.rating; }, 0) / data.items.length || 0;
        const avgEl = document.getElementById('average-rating');
        if (avgEl) avgEl.textContent = avgRating.toFixed(1);
        const cntEl = document.getElementById('review-count');
        if (cntEl) cntEl.textContent = '(' + data.total + ' reviews)';
        const starsContainer = document.getElementById('rating-stars');
        if (starsContainer) {
            starsContainer.innerHTML = '';
            for (let i = 1; i <= 5; i++) {
                const star = document.createElement('span');
                star.className = i <= Math.floor(avgRating) ? 'star-filled' : 'star-empty';
                star.textContent = String.fromCharCode(9733);
                starsContainer.appendChild(star);
            }
        }
    }

    createReviewCard(review) {
        const card = document.createElement('div');
        card.className = 'review-card';
        const date = new Date(review.published_at || review.created_at);
        const formattedDate = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        const verified = review.verified_purchase ? '<span class="verified-badge">Verified Purchase</span>' : '';
        const status = review.status === 'approved' ? '<span>• Approved</span>' : '<span>• ' + review.status + '</span>';
        card.innerHTML = '<div class="review-header"><div class="reviewer-info"><span class="reviewer-name">' + this.escapeHtml(review.reviewer_name) + '</span>' + verified + '</div><div class="review-rating">' + this.createStarsHtml(review.rating) + '</div></div><h3 class="review-title">' + this.escapeHtml(review.title) + '</h3><p class="review-content">' + this.escapeHtml(review.content) + '</p><div class="review-meta"><span>' + formattedDate + '</span>' + status + '</div>';
        return card;
    }

    createStarsHtml(rating) {
        let stars = '';
        const fullStars = Math.floor(rating);
        for (let i = 1; i <= 5; i++) {
            const cls = i <= fullStars ? 'star-filled' : 'star-empty';
            stars += '<span class="' + cls + '">' + String.fromCharCode(9733) + '</span>';
        }
        return stars;
    }

    setupReviewForm() {
        const writeReviewBtn = document.getElementById('write-review-btn');
        if (!writeReviewBtn) return;
        const self = this;
        writeReviewBtn.addEventListener('click', function() { self.openReviewModal(); });
        document.querySelectorAll('.rating-star').forEach(function(star) {
            star.addEventListener('click', function(e) { self.selectRating(parseInt(e.target.dataset.rating)); });
            star.addEventListener('mouseover', function(e) { self.previewRating(parseInt(e.target.dataset.rating)); });
            star.addEventListener('mouseout', function() { self.previewRating(self.selectedRating); });
        });
        const reviewForm = document.getElementById('review-form');
        if (reviewForm) reviewForm.addEventListener('submit', function(e) { self.submitReview(e); });
        const closeBtn = document.getElementById('close-review-modal');
        if (closeBtn) closeBtn.addEventListener('click', function() { self.closeReviewModal(); });
        const cancelBtn = document.getElementById('cancel-review');
        if (cancelBtn) cancelBtn.addEventListener('click', function() { self.closeReviewModal(); });
        const modal = document.getElementById('review-modal');
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) self.closeReviewModal();
            });
        }
    }

    selectRating(rating) {
        this.selectedRating = rating;
        this.updateRatingDisplay();
        const hidden = document.getElementById('review-rating');
        if (hidden) hidden.value = rating;
    }

    previewRating(rating) {
        document.querySelectorAll('.rating-star').forEach(function(star, index) {
            star.style.color = index < rating ? '#fbbf24' : '#d1d5db';
        });
    }

    updateRatingDisplay() {
        const self = this;
        document.querySelectorAll('.rating-star').forEach(function(star, index) {
            if (index < self.selectedRating) {
                star.classList.add('active');
                star.style.color = '#fbbf24';
            } else {
                star.classList.remove('active');
                star.style.color = '#d1d5db';
            }
        });
        const helpText = document.getElementById('rating-help');
        if (helpText) {
            helpText.textContent = self.selectedRating ? 'Rating ' + self.selectedRating + '/5' : 'Select rating';
        }
    }

    openReviewModal() {
        const modal = document.getElementById('review-modal');
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            this.resetReviewForm();
        }
    }

    closeReviewModal() {
        const modal = document.getElementById('review-modal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    resetReviewForm() {
        const form = document.getElementById('review-form');
        if (form) form.reset();
        this.selectedRating = 0;
        this.updateRatingDisplay();
        const hidden = document.getElementById('review-rating');
        if (hidden) hidden.value = '';
    }

    async submitReview(e) {
        e.preventDefault();
        const titleEl = document.getElementById('review-title');
        const contentEl = document.getElementById('review-content');
        if (!titleEl || !contentEl) return;
        const formData = { title: titleEl.value.trim(), content: contentEl.value.trim(), rating: this.selectedRating };
        if (!formData.title || !formData.content || !formData.rating) {
            alert('Please fill in all fields and select a rating');
            return;
        }
        try {
            await window.api.request('/products/' + this.productId + '/reviews', {
                method: 'POST',
                body: JSON.stringify(formData)
            });
            alert('Thank you for your review! It will be visible after admin approval.');
            this.closeReviewModal();
            this.loadProductReviews();
        } catch (error) {
            alert(error.message || 'Failed to submit review. Please try again.');
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    window.reviewsSystem = new ReviewsSystem();
});
