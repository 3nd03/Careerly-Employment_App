import { Link } from 'react-router-dom'

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-[640px] bg-mint-light border border-mint-border rounded-xl p-6">
        <h1 className="text-2xl font-bold text-teal text-center">Careerly</h1>
        <div className="border-t border-mint my-6" />

        <h2 className="text-xl font-bold text-teal">Privacy Policy</h2>
        <p className="text-body text-sm mt-1 mb-6">
          Careerly is a prototype built for a charity hackathon. This explains what we collect and why in plain
          terms, not a legal document.
        </p>

        <div className="space-y-5 text-sm text-body">
          <section>
            <h3 className="font-bold text-teal mb-1">What we collect</h3>
            <p>
              Your email, name, and password (stored as a hash, never in plain text). Answers you give during
              onboarding (target role, skills, background, experience, and any access needs you choose to share).
              Any CV you upload, including the text extracted from it. A profile photo if you choose to add one.
              The results each tool generates for you.
            </p>
          </section>

          <section>
            <h3 className="font-bold text-teal mb-1">Why we collect it</h3>
            <p>
              Solely to run the tools you use, for example matching your profile against a target role, or
              rewriting your CV. Your profile and CV text are sent to Anthropic's Claude API to generate these
              results. Nothing is sold, and nothing is used to train a model.
            </p>
          </section>

          <section>
            <h3 className="font-bold text-teal mb-1">How long we keep it</h3>
            <p>
              Your data is kept for as long as your account exists. There is no automatic expiry. You can delete
              your account and everything tied to it at any time from your Profile page.
            </p>
          </section>

          <section>
            <h3 className="font-bold text-teal mb-1">Deleting your data</h3>
            <p>
              Signed-in users can permanently delete their account from Profile &rarr; Danger zone. This removes
              your account, every profile, and every saved result, and deletes any CV or avatar files stored for
              you.
            </p>
          </section>

          <section>
            <h3 className="font-bold text-teal mb-1">Who can see your data</h3>
            <p>
              Only you, through your account. The small team running this prototype can access the underlying
              database and storage for maintenance and debugging, since this is a hackathon project rather than a
              production service with formal access controls.
            </p>
          </section>
        </div>

        <div className="border-t border-mint my-6" />
        <p className="text-center text-sm text-body">
          <Link to="/signup" className="text-teal font-medium">
            Back to sign up
          </Link>
        </p>
      </div>
    </div>
  )
}
