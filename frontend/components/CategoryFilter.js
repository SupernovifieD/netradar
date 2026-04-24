// components/CategoryFilter.js
export default function CategoryFilter({ selected, onSelect }) {
  const categories = [
    'همه',
    'عمومی خارجی',
    'عمومی داخلی',
    'تخصصی خارجی',
    'تخصصی داخلی'
  ];

  return (
    <div className="flex flex-wrap gap-2 mb-8">
      {categories.map(cat => (
        <button
          key={cat}
          onClick={() => onSelect(cat)}
          className={`px-4 py-2 rounded border transition-colors ${
            selected === cat
              ? 'bg-blue-600 border-blue-600 text-white'
              : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
          }`}
        >
          {cat}
        </button>
      ))}
    </div>
  );
}
