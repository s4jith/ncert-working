import { useState } from 'react';
import { ChevronLeft, ChevronRight, Plus, X, Upload } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';

/**
 * ExamCalendar Step (Step 4)
 * 
 * OPTIONAL step - add exam dates manually or upload timetable.
 * Enables reminders, revision planning, and dashboard insights.
 * 
 * TODO: Backend Integration
 * - POST /api/onboarding/calendar
 * - Store exam dates
 * - Could integrate OCR for timetable upload
 */

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function ExamCalendar({ data, onNext, onSkip }) {
  const [exams, setExams] = useState(data.exams || []);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [newExam, setNewExam] = useState({ subject: '', date: '' });

  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  const getDaysInMonth = (month, year) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (month, year) => {
    return new Date(year, month, 1).getDay();
  };

  const navigateMonth = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentMonth + direction);
    setCurrentDate(newDate);
  };

  const formatDate = (date) => {
    return `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`;
  };

  const getExamsForDate = (date) => {
    const dateStr = formatDate(date);
    return exams.filter(exam => exam.date === dateStr);
  };

  const handleDateClick = (date) => {
    const dateStr = formatDate(date);
    setSelectedDate(dateStr);
    setNewExam({ ...newExam, date: dateStr });
    setShowAddForm(true);
  };

  const addExam = () => {
    if (newExam.subject && newExam.date) {
      setExams([...exams, { ...newExam, id: Date.now() }]);
      setNewExam({ subject: '', date: '' });
      setShowAddForm(false);
      setSelectedDate(null);
    }
  };

  const removeExam = (id) => {
    setExams(exams.filter(exam => exam.id !== id));
  };

  const handleNext = () => {
    /**
     * TODO: Backend Integration
     * await fetch('/api/onboarding/calendar', {
     *   method: 'POST',
     *   body: JSON.stringify({ exams })
     * });
     */
    onNext({ exams });
  };

  // Generate calendar grid
  const daysInMonth = getDaysInMonth(currentMonth, currentYear);
  const firstDay = getFirstDayOfMonth(currentMonth, currentYear);
  const calendarDays = [];

  // Empty cells for days before the first day of the month
  for (let i = 0; i < firstDay; i++) {
    calendarDays.push(null);
  }

  // Days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push(day);
  }

  return (
    <div className="max-w-lg mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Exam Calendar
        </h2>
        <p className="text-muted-foreground">
          Add your exam dates for personalized revision planning
        </p>
      </div>

      {/* Calendar */}
      <div className="border rounded-lg p-4 mb-6 bg-card">
        {/* Month Navigation */}
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => navigateMonth(-1)}
            className="p-2 hover:bg-secondary rounded-lg transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h3 className="text-lg font-semibold text-foreground">
            {MONTHS[currentMonth]} {currentYear}
          </h3>
          <button
            onClick={() => navigateMonth(1)}
            className="p-2 hover:bg-secondary rounded-lg transition-colors"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        {/* Weekday Headers */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {WEEKDAYS.map((day) => (
            <div
              key={day}
              className="text-center text-xs font-medium text-muted-foreground py-2"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-1">
          {calendarDays.map((day, index) => {
            if (day === null) {
              return <div key={`empty-${index}`} className="p-2" />;
            }

            const dayExams = getExamsForDate(day);
            const isToday =
              new Date().getDate() === day &&
              new Date().getMonth() === currentMonth &&
              new Date().getFullYear() === currentYear;

            return (
              <button
                key={day}
                onClick={() => handleDateClick(day)}
                className={`relative p-2 rounded-lg text-center transition-colors ${
                  isToday
                    ? 'bg-foreground text-background'
                    : 'hover:bg-secondary'
                } ${dayExams.length > 0 ? 'font-semibold' : ''}`}
              >
                {day}
                {dayExams.length > 0 && (
                  <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-destructive rounded-full" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Add Exam Form */}
      {showAddForm && (
        <div className="border rounded-lg p-4 mb-6 bg-secondary/50">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-foreground">Add Exam</h4>
            <button
              onClick={() => {
                setShowAddForm(false);
                setSelectedDate(null);
              }}
              className="text-muted-foreground hover:text-foreground"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-sm text-muted-foreground mb-1">
                Date: {selectedDate}
              </label>
            </div>
            <div>
              <Input
                type="text"
                value={newExam.subject}
                onChange={(e) => setNewExam({ ...newExam, subject: e.target.value })}
                placeholder="Subject name (e.g., Mathematics Unit Test)"
                className="h-10"
              />
            </div>
            <Button
              onClick={addExam}
              disabled={!newExam.subject}
              size="sm"
              className="w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Exam
            </Button>
          </div>
        </div>
      )}

      {/* Added Exams List */}
      {exams.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-foreground mb-2">
            Scheduled Exams
          </h4>
          <div className="space-y-2">
            {exams.map((exam) => (
              <div
                key={exam.id}
                className="flex items-center justify-between p-3 bg-card border rounded-lg"
              >
                <div>
                  <p className="font-medium text-foreground">{exam.subject}</p>
                  <p className="text-xs text-muted-foreground">{exam.date}</p>
                </div>
                <button
                  onClick={() => removeExam(exam.id)}
                  className="p-1 text-muted-foreground hover:text-destructive transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Option */}
      <div className="mb-6">
        <div className="border-2 border-dashed rounded-lg p-6 text-center">
          <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm text-muted-foreground mb-2">
            Or upload your exam timetable
          </p>
          <Button variant="outline" size="sm" disabled>
            Upload PDF/Image
          </Button>
          <p className="text-xs text-muted-foreground mt-2">
            (Coming soon)
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button
          variant="outline"
          onClick={onSkip}
          className="flex-1 h-12"
        >
          Skip for now
        </Button>
        <Button
          onClick={handleNext}
          className="flex-1 h-12"
        >
          {exams.length > 0 ? 'Save' : 'Finish'}
        </Button>
      </div>
    </div>
  );
}

export default ExamCalendar;
