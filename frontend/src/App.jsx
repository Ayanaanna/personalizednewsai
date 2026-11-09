
import { useEffect, useState } from "react";

function App() {
  const [expandedSummary, setExpandedSummary] = useState(null);

  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  const [selectedInterest, setSelectedInterest] = useState("All");

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [asking, setAsking] = useState(false);

  const interests = [
    "All",
    "AI",
    "Technology",
    "Startups",
    "Business",
    "Science",
    "Space",
    "Sports",
    "Movies",
    "World",
  ];

  function selectInterest(interest) {
    setSelectedInterest(interest);
    setExpandedSummary(null);
  }

  useEffect(() => {
    setLoading(true);
    setArticles([]);
    setExpandedSummary(null);

    let interestsQuery = "";

    if (selectedInterest !== "All") {
      interestsQuery = selectedInterest;
    }

    fetch(
      `http://127.0.0.1:8000/articles?interests=${encodeURIComponent(
        interestsQuery
      )}`
    )
      .then((response) => response.json())
      .then((data) => {
        setArticles(data.articles || []);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching news:", error);
        setArticles([]);
        setLoading(false);
      });
  }, [selectedInterest]);

  async function askQuestion() {
    if (!question.trim()) {
      return;
    }

    setAsking(true);
    setAnswer("");
    setSources([]);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/ask?question=${encodeURIComponent(
          question
        )}`
      );

      const data = await response.json();

      setAnswer(data.answer || "No answer available.");
      setSources(data.sources || []);
    } catch (error) {
      console.error("Error asking question:", error);
      setAnswer("Unable to connect to the news assistant.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#080b14] text-white">

      {/* Header */}
      <header className="border-b border-white/10 bg-[#0b0f1a]/90 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">

          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              ✦ NewsAI
            </h1>

            <p className="text-xs text-gray-500 mt-1">
              Intelligent news, personalized for you
            </p>
          </div>

          <div className="flex items-center gap-3">

            <button
              className="w-10 h-10 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition"
              title="Search"
            >
              🔍
            </button>

            <button
              className="w-10 h-10 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition"
              title="Dark mode"
            >
              🌙
            </button>

            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center font-semibold">
              A
            </div>

          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-10">

        {/* Hero */}
        <section className="mb-10">

          <p className="text-blue-400 text-sm font-medium mb-3">
            YOUR PERSONAL NEWS FEED
          </p>

          <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
            Your news.
            <span className="text-blue-400">
              {" "}Powered by AI.
            </span>
          </h2>

          <p className="text-gray-400 mt-4 max-w-2xl">
            Discover the stories that matter to you and ask AI
            questions about the latest news.
          </p>

        </section>

        {/* Categories */}
        <section className="mb-10">

          <div className="flex gap-3 overflow-x-auto pb-3">

            {interests.map((interest) => {
              const active =
                selectedInterest === interest;

              return (
                <button
                  key={interest}
                  onClick={() => selectInterest(interest)}
                  className={`whitespace-nowrap px-5 py-2.5 rounded-full border text-sm font-medium transition ${
                    active
                      ? "bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-600/20"
                      : "bg-white/5 border-white/10 text-gray-400 hover:text-white hover:bg-white/10"
                  }`}
                >
                  {interest}
                </button>
              );
            })}

          </div>

        </section>

        {/* Ask the News */}
        <section className="mb-12">

          <div className="relative overflow-hidden rounded-2xl border border-blue-500/20 bg-gradient-to-br from-[#10182b] to-[#0c111f] p-6 md:p-8">

            <div className="absolute -top-20 -right-20 w-60 h-60 bg-blue-600/10 rounded-full blur-3xl"></div>

            <div className="relative">

              <div className="flex items-center gap-3 mb-2">

                <div className="w-10 h-10 rounded-xl bg-blue-600/20 flex items-center justify-center">
                  ✨
                </div>

                <h2 className="text-2xl font-semibold">
                  Ask the News
                </h2>

              </div>

              <p className="text-gray-400 mb-6">
                Ask questions about the latest news and get
                AI-powered answers.
              </p>

              <div className="flex flex-col md:flex-row gap-3">

                <input
                  type="text"
                  value={question}
                  onChange={(event) =>
                    setQuestion(event.target.value)
                  }
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      askQuestion();
                    }
                  }}
                  placeholder="What is happening with NASA?"
                  className="flex-1 bg-black/20 border border-white/10 rounded-xl px-5 py-4 text-white placeholder-gray-500 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                />

                <button
                  onClick={askQuestion}
                  disabled={
                    asking ||
                    !question.trim()
                  }
                  className="px-7 py-4 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 font-medium transition"
                >
                  {asking ? "Thinking..." : "Ask →"}
                </button>

              </div>

              {/* AI Answer */}
              {answer && (
                <div className="mt-6 rounded-xl bg-black/20 border border-white/10 p-6">

                  <div className="flex items-center gap-2 mb-4">

                    <span className="text-blue-400">
                      ✦
                    </span>

                    <h3 className="font-semibold">
                      AI Answer
                    </h3>

                  </div>

                  <p className="text-gray-300 leading-relaxed whitespace-pre-line">
                    {answer
                      .replace(/\*\*Sources:\*\*/gi, "")
                      .replace(/Sources:/gi, "")
                      .replace(/\*\*/g, "")
                      .replace(/^\s*[-*]\s*$/gm, "")
                      .replace(/https?:\/\/\S+/g, "")
                      .trim()}
                  </p>

                  {/* Sources */}
                  {sources.length > 0 && (
                    <div className="mt-6 pt-5 border-t border-white/10">

                      <p className="text-sm font-semibold text-gray-300 mb-3">
                        Sources
                      </p>

                      <div className="space-y-2">

                        {sources.map((source, index) => (
                          <a
                            key={index}
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block text-sm text-blue-400 hover:text-blue-300 hover:underline"
                          >
                            {source.source}: {source.title}
                          </a>
                        ))}

                      </div>

                    </div>
                  )}

                </div>
              )}

            </div>

          </div>

        </section>

        {/* News */}
        <section>

          <div className="flex items-end justify-between mb-6">

            <div>

              <p className="text-blue-400 text-xs font-semibold uppercase tracking-wider mb-2">
                Curated for you
              </p>

              <h2 className="text-2xl font-semibold">
                {selectedInterest === "All"
                  ? "Latest News"
                  : `${selectedInterest} News`}
              </h2>

            </div>

            <span className="text-sm text-gray-500">
              {articles.length} stories
            </span>

          </div>

          {/* Loading */}
          {loading && (
            <div className="grid md:grid-cols-2 gap-6">

              {[1, 2, 3, 4].map((item) => (
                <div
                  key={item}
                  className="h-80 rounded-2xl bg-white/5 animate-pulse"
                ></div>
              ))}

            </div>
          )}

          {/* Articles */}
          {!loading && articles.length > 0 && (
            <div className="grid md:grid-cols-2 gap-6">

              {articles.map((article, index) => (

                <article
                  key={article.url || index}
                  className="group bg-[#101521] border border-white/10 rounded-2xl overflow-hidden hover:border-blue-500/30 hover:-translate-y-1 transition duration-300"
                >

                  {/* Image */}
                  {article.image ? (
                    <div className="overflow-hidden">

                      <img
                        src={article.image}
                        alt={article.title}
                        className="w-full h-56 object-cover group-hover:scale-105 transition duration-500"
                      />

                    </div>
                  ) : (
                    <div className="w-full h-56 bg-[#151b29] flex items-center justify-center text-gray-600">
                      No image available
                    </div>
                  )}

                  {/* Article Content */}
                  <div className="p-6">

                    <div className="flex items-center justify-between mb-3">

                      <span className="text-xs font-semibold text-blue-400 uppercase">
                        {article.source}
                      </span>

                    </div>

                    <h3 className="text-xl font-semibold leading-snug group-hover:text-blue-400 transition">
                      {article.title}
                    </h3>

                    <p className="text-xs text-gray-500 mt-4">
                      {article.published_at}
                    </p>

                    {/* AI Summary Button */}
                    <button
                      onClick={() => {
                        if (expandedSummary === index) {
                          setExpandedSummary(null);
                        } else {
                          setExpandedSummary(index);
                        }
                      }}
                      className="mt-5 flex items-center gap-2 text-sm font-medium text-purple-400 hover:text-purple-300 transition"
                    >
                      {expandedSummary === index
                        ? "▾ Hide AI Summary"
                        : "▸ Show AI Summary"}
                    </button>

                    {/* AI Summary */}
                    {expandedSummary === index && (
                      <div className="mt-4 rounded-xl border border-purple-500/20 bg-purple-500/5 p-5">

                        <div className="flex items-center gap-2 mb-3">

                          <span className="text-purple-400">
                            ✦
                          </span>

                          <h4 className="text-sm font-semibold text-purple-300 uppercase tracking-wide">
                            AI Summary
                          </h4>

                        </div>

                        <p className="text-sm leading-6 text-gray-300">
                          {article.ai_summary ||
                            "AI summary is not available for this article."}
                        </p>

                      </div>
                    )}

                    {/* Read Full Story */}
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block mt-5 text-sm font-medium text-blue-400 hover:text-blue-300"
                    >
                      Read full story →
                    </a>

                  </div>

                </article>

              ))}

            </div>
          )}

          {/* No Articles */}
          {!loading && articles.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/5 p-10 text-center">

              <p className="text-gray-400">
                No matching news found.
              </p>

              <p className="text-sm text-gray-600 mt-2">
                Select another category to discover more stories.
              </p>

            </div>
          )}

        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 mt-16">

        <div className="max-w-7xl mx-auto px-6 py-8 text-center">

          <p className="text-sm text-gray-600">
            NewsAI • Personalized with AI & RAG
          </p>

        </div>

      </footer>

    </div>
  );
}

export default App;

