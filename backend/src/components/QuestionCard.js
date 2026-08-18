import React, { useState, useEffect } from "react";
import "./QuestionCard.css";

export default function QuestionCard({
  question,
  index,
  total,
  onAnswer,
  feedback,
  isLoading,
}) {
  const [selected, setSelected] = useState("");
  const [openAnswer, setOpenAnswer] = useState("");

  useEffect(() => {
    setSelected("");
    setOpenAnswer("");
  }, [question]);

  const isAnswered = feedback !== null && feedback !== undefined;

  const handleSubmit = () => {
    const userAnswer = question.type === "aperta" ? openAnswer : selected;
    if (!userAnswer.trim()) return;
    onAnswer(userAnswer);
  };

  const typeLabel = {
    multipla: "Scelta multipla",
    vero_falso: "Vero o Falso",
    aperta: "Domanda aperta",
  }[question.type] || question.type;

  return (
    <div className="qcard">
      <div className="qcard-header">
        <span className="qcard-progress">
          Domanda {index + 1} / {total}
        </span>
        <span className="qcard-type">{typeLabel}</span>
      </div>

      <h2 className="qcard-question">{question.question}</h2>

      {question.type === "multipla" && (
        <div className="qcard-options">
          {question.options?.map((opt, i) => (
            <label
              key={i}
              className={`qcard-option ${selected === opt ? "selected" : ""} ${
                isAnswered ? "disabled" : ""
              }`}
            >
              <input
                type="radio"
                name={`q-${index}`}
                value={opt}
                checked={selected === opt}
                onChange={() => setSelected(opt)}
                disabled={isAnswered}
              />
              {opt}
            </label>
          ))}
        </div>
      )}

      {question.type === "vero_falso" && (
        <div className="qcard-options qcard-options-inline">
          {["Vero", "Falso"].map((opt) => (
            <label
              key={opt}
              className={`qcard-option ${selected === opt ? "selected" : ""} ${
                isAnswered ? "disabled" : ""
              }`}
            >
              <input
                type="radio"
                name={`q-${index}`}
                value={opt}
                checked={selected === opt}
                onChange={() => setSelected(opt)}
                disabled={isAnswered}
              />
              {opt}
            </label>
          ))}
        </div>
      )}

      {question.type === "aperta" && (
        <textarea
          className="qcard-textarea"
          rows={3}
          placeholder="Scrivi qui la tua risposta..."
          value={openAnswer}
          onChange={(e) => setOpenAnswer(e.target.value)}
          disabled={isAnswered}
        />
      )}

      {!isAnswered && (
        <button
          className="btn btn-primary qcard-submit"
          onClick={handleSubmit}
          disabled={
            isLoading ||
            (question.type === "aperta" ? !openAnswer.trim() : !selected)
          }
        >
          {isLoading ? "Valutazione..." : "Conferma risposta"}
        </button>
      )}

      {isAnswered && (
        <div className={`qcard-feedback ${feedback.isCorrect ? "correct" : "incorrect"}`}>
