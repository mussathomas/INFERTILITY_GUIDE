import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="landing-page">
      <nav className="landing-nav">
        <span className="logo-link">UZAZI ASSISTANT</span>
        <div className="landing-nav-actions">
          <Link to="/login" className="btn btn-ghost">Sign in</Link>
          <Link to="/register" className="btn btn-primary">Get started</Link>
        </div>
      </nav>

      <section className="hero">
      <span className="hero-badge">UZAZI ASSISTANT</span>
        <h1>
          Trusted guidance for<br />
          <em>infertility questions</em>
        </h1>
        <p className="hero-desc">
          A compassionate chat assistant grounded in verified resources. Get accurate answers,
          myth correction, and balanced traditional medicine guidance — all in one place.
        </p>
        <div className="hero-actions">
          <Link to="/register" className="btn btn-primary btn-lg">Start free</Link>
          <Link to="/login" className="btn btn-outline btn-lg">Sign in</Link>
        </div>
      </section>

      <section className="features-grid">
        <article className="feature-card">
          <h3>Evinced and Trusted knowledge base</h3>
          <p>Responses are retrieved from curated, evidence-based sources on infertility.</p>
        </article>
        <article className="feature-card">
          <h3>Misinformation correction</h3>
          <p>Common myths are identified and corrected with clear, supportive explanations.</p>
        </article>
        <article className="feature-card">
          <h3>Traditional medicine guidance</h3>
          <p>MUHAS,Ethnomedicine, and herbal approaches are discussed with cultural respect and medical balance.</p>
        </article>
        <article className="feature-card">
          <h3>Secure accounts</h3>
          <p>Register and log in to save your conversation history privately.</p>
        </article>
      </section>

      <footer className="landing-footer">
        <p>
          FertilityGuide provides educational information only. It is not a substitute for professional medical care.
        </p>
      </footer>
    </div>
  );
}
