import React, { useState } from 'react';
import { Star, Send, Flag, CheckCircle } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { apiClient } from '../../api/client';

interface FeedbackModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  queryId: string;
  queryText: string;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  open,
  onOpenChange,
  queryId,
  queryText,
}) => {
  const [rating, setRating] = useState<number>(5);
  const [flagIncorrect, setFlagIncorrect] = useState<boolean>(false);
  const [correction, setCorrection] = useState<string>('');
  const [comment, setComment] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage('');

    try {
      await apiClient.submitFeedback({
        query_id: queryId,
        rating,
        flagged_incorrect: flagIncorrect,
        correction: correction.trim() || null,
        comment: comment.trim() || null,
      });
      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        onOpenChange(false);
      }, 1500);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to submit feedback');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title="Submit Grounded Feedback"
      description="Help continuously improve the enterprise knowledge base and active learning feedback loop."
    >
      {submitted ? (
        <div className="py-8 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
            <CheckCircle className="w-6 h-6" />
          </div>
          <h4 className="text-base font-bold text-slate-100">Feedback Recorded</h4>
          <p className="text-xs text-slate-400">
            Thank you! Your feedback has been queued for active learning review.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <span className="font-semibold text-slate-400 block mb-1">Inquiry:</span>
            <span className="text-slate-200 font-medium line-clamp-2">"{queryText}"</span>
          </div>

          {/* Rating */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Accuracy & Helpfulness Rating
            </label>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  className="p-1 text-slate-600 hover:text-amber-400 transition-colors"
                >
                  <Star
                    className={`w-6 h-6 ${
                      star <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-600'
                    }`}
                  />
                </button>
              ))}
              <span className="text-xs font-bold text-slate-300 ml-2">{rating} / 5 Stars</span>
            </div>
          </div>

          {/* Flag as incorrect */}
          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="flag-incorrect"
              checked={flagIncorrect}
              onChange={(e) => setFlagIncorrect(e.target.checked)}
              className="rounded accent-rose-500 w-4 h-4"
            />
            <label htmlFor="flag-incorrect" className="text-xs text-slate-300 flex items-center gap-1 cursor-pointer">
              <Flag className="w-3.5 h-3.5 text-rose-400" />
              Flag this response as factually unsupported or hallucinated
            </label>
          </div>

          {/* Human correction input */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Correct Answer (Optional)
            </label>
            <textarea
              rows={2}
              value={correction}
              onChange={(e) => setCorrection(e.target.value)}
              placeholder="Provide the accurate policy or technical remediation..."
              className="w-full text-xs bg-slate-900 border border-slate-700/80 rounded-xl p-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
          </div>

          {/* General comments */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Qualitative Notes / Citation Discrepancies
            </label>
            <textarea
              rows={2}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="e.g. Missing warranty exclusion clauses in response..."
              className="w-full text-xs bg-slate-900 border border-slate-700/80 rounded-xl p-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
          </div>

          {errorMessage && (
            <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-500/30 text-rose-300 text-xs">
              {errorMessage}
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              loading={loading}
              icon={<Send className="w-3.5 h-3.5" />}
            >
              Submit Feedback
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
};
