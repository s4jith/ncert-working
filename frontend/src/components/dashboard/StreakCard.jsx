import { useState, useEffect } from "react";
import { Flame, Loader2 } from "lucide-react";
import { userStatsService } from "../../services/api";
import useUserStore from "../../stores/userStore";

/**
 * StreakCard Component
 * 
 * Displays user's activity streak and weekly activity chart.
 * Fetches real data from MongoDB via backend API.
 */

export default function StreakCard() {
  const { user } = useUserStore();
  const [streakData, setStreakData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const generateEmptyWeek = () => {
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const today = new Date();
    return days.map((day, i) => ({
      day,
      active: false,
      hours: 0,
      date: new Date(today - (6 - i) * 86400000).toISOString().split("T")[0]
    }));
  };

  useEffect(() => {
    const fetchStreakData = async () => {
      const studentId = user.id || "guest";

      try {
        setLoading(true);
        const data = await userStatsService.getStreakData(studentId);
        setStreakData(data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch streak data:", err);
        setError(err.message);
        // Use fallback data on error
        setStreakData({
          current_streak: 0,
          longest_streak: 0,
          weekly_activity: generateEmptyWeek()
        });
      } finally {
        setLoading(false);
      }
    };

    fetchStreakData();
  }, [user.id]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  const currentStreak = streakData?.current_streak || 0;
  const longestStreak = streakData?.longest_streak || 0;
  const weeklyActivity = streakData?.weekly_activity || generateEmptyWeek();
  
  const maxHours = Math.max(...weeklyActivity.map(d => d.hours), 1);

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Activity Streak</h3>
        <div className="flex items-center gap-2 px-3 py-1 bg-orange-100 rounded-full">
          <Flame className="w-4 h-4 text-orange-500" />
          <span className="text-orange-600 font-bold">{currentStreak} days</span>
        </div>
      </div>

      {/* Weekly Activity Chart */}
      <div className="flex items-end justify-between gap-2 h-24 mb-4">
        {weeklyActivity.map((day, index) => (
          <div key={index} className="flex-1 flex flex-col items-center gap-1">
            <div 
              className="w-full rounded-t-lg transition-all duration-300"
              style={{ 
                height: `${Math.max((day.hours / maxHours) * 100, 8)}%`,
                backgroundColor: day.active ? '#ffc801' : '#e5e7eb',
                minHeight: '8px'
              }}
              title={`${day.hours}h on ${day.date}`}
            />
            <span className="text-xs text-gray-500">{day.day}</span>
          </div>
        ))}
      </div>

      {/* Stats Row */}
      <div className="flex justify-between text-sm pt-3 border-t border-gray-100">
        <div>
          <span className="text-gray-500">Current Streak</span>
          <p className="font-semibold text-gray-800">{currentStreak} days</p>
        </div>
        <div className="text-right">
          <span className="text-gray-500">Longest Streak</span>
          <p className="font-semibold text-gray-800">{longestStreak} days</p>
        </div>
      </div>

      {error && (
        <p className="text-xs text-amber-500 mt-2 text-center">
          Using offline data
        </p>
      )}
    </div>
  );
}
