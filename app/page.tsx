export default function Home() {
  return (
    <main className="app-shell">
      <iframe
        className="dashboard-frame"
        src="/dashboard.html"
        title="مرآة — قارن الدول بالأرقام"
      />
    </main>
  );
}
