import { Link } from "react-router-dom";

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  alternateText: string;
  alternateLink: string;
  alternateLabel: string;
}

export function AuthLayout({
  title,
  subtitle,
  children,
  alternateText,
  alternateLink,
  alternateLabel,
}: AuthLayoutProps) {
  return (
    <div className="auth-page">
      <div className="auth-panel auth-panel--brand">
        <div className="brand-content">
          <span className="brand-badge">Evidence-informed guidance</span>
          <h1 className="brand-title">
            Compassionate answers about <em>Infertility</em>
          </h1>
          <p className="brand-desc">
            Ask questions, get verified information from our verified knowledge base, and receive gentle
            correction of common myths — including balanced guidance on traditional medicine.
          </p>
          <ul className="brand-features">
            <li>Verified knowledge base</li>
            <li>Misinformation correction</li>
            <li>Traditional medicine guidance</li>
            <li>Powered large language models</li>
          </ul>
        </div>
      </div>

      <div className="auth-panel auth-panel--form">
        <div className="auth-form-wrap">
          <Link to="/" className="logo-link">
            FertilityGuide
          </Link>
          <h2>{title}</h2>
          <p className="auth-subtitle">{subtitle}</p>
          {children}
          <p className="auth-alternate">
            {alternateText}{" "}
            <Link to={alternateLink}>{alternateLabel}</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
