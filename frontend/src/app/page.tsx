import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-gray-900 dark:to-indigo-950">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-4 text-gray-900 dark:text-white">
          Tarot AI Reading Service
        </h1>
        <p className="text-center mb-8 text-gray-600 dark:text-gray-300">
          AI 기반 타로 카드 리딩 서비스
        </p>

        <div className="mb-12 grid text-center lg:mb-0 lg:w-full lg:max-w-5xl lg:grid-cols-3 lg:text-left gap-4">
          <Link
            href="/reading/one-card"
            className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 dark:hover:border-neutral-700 dark:hover:bg-neutral-800/30"
          >
            <h2 className="mb-3 text-2xl font-semibold">
              원카드 리딩
              <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
                →
              </span>
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              오늘의 운세를 한 장의 카드로 확인하세요
            </p>
          </Link>

          <Link
            href="/reading/three-card"
            className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 dark:hover:border-neutral-700 dark:hover:bg-neutral-800/30"
          >
            <h2 className="mb-3 text-2xl font-semibold">
              쓰리카드 리딩
              <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
                →
              </span>
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              과거-현재-미래를 세 장의 카드로 살펴보세요
            </p>
          </Link>

          <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 dark:hover:border-neutral-700 dark:hover:bg-neutral-800/30 relative">
            <div className="absolute top-2 right-2 px-2 py-1 bg-yellow-500 text-xs font-bold rounded">
              Coming Soon
            </div>
            <h2 className="mb-3 text-2xl font-semibold text-gray-400">
              상세 리딩
              <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
                →
              </span>
            </h2>
            <p className="m-0 max-w-[30ch] text-sm opacity-50">
              AI가 제공하는 심층적인 타로 해석
            </p>
          </div>
        </div>

        <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/history"
            className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-semibold"
          >
            📖 리딩 히스토리
          </Link>
          <Link
            href="/cards"
            className="inline-block px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-semibold"
          >
            📚 타로 카드 컬렉션 보기
          </Link>
        </div>

        <div className="mt-16 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Powered by OpenAI & Anthropic Claude
          </p>
        </div>
      </div>
    </main>
  );
}
