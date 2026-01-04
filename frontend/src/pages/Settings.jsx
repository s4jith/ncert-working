import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  User, 
  GraduationCap, 
  Palette, 
  Calendar, 
  Shield, 
  ArrowLeft,
  Save,
  Plus,
  X,
  RefreshCw,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import useUserStore from '../stores/userStore';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import classesData from '../data/classes.json';

/**
 * Settings Page
 * 
 * Comprehensive settings page with horizontal tab navigation.
 * Allows editing all profile data set during onboarding plus privacy settings.
 */

const TABS = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'academics', label: 'Academics', icon: GraduationCap },
  { id: 'avatar', label: 'Avatar', icon: Palette },
  { id: 'calendar', label: 'Calendar', icon: Calendar },
  { id: 'privacy', label: 'Privacy', icon: Shield },
];

const AVATAR_STYLES = [
  { id: 'avataaars', name: 'Avatars' },
  { id: 'bottts', name: 'Robots' },
  { id: 'lorelei', name: 'Lorelei' },
  { id: 'micah', name: 'Micah' },
  { id: 'notionists', name: 'Notion' }
];

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function Settings() {
  const navigate = useNavigate();
  const { 
    user, 
    academics, 
    calendar, 
    privacySettings, 
    updateProfile, 
    updateAcademics, 
    updateCalendar, 
    updatePrivacySettings 
  } = useUserStore();
  
  const [activeTab, setActiveTab] = useState('profile');
  const [saveMessage, setSaveMessage] = useState('');

  // Profile state
  const [profileData, setProfileData] = useState({
    name: user.name || '',
    classLevel: user.classLevel || 6,
    username: user.username || '',
  });

  // Academics state
  const [subjects, setSubjects] = useState(academics.subjects || []);
  const [showAddSubject, setShowAddSubject] = useState(false);
  const [newSubject, setNewSubject] = useState({ name: '', marks: '' });

  // Avatar state
  const [avatarSeed, setAvatarSeed] = useState(user.avatarSeed || Date.now().toString());
  const [avatarStyle, setAvatarStyle] = useState(user.avatarStyle || 'avataaars');

  // Calendar state
  const [exams, setExams] = useState(calendar.exams || []);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [showAddExam, setShowAddExam] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [newExam, setNewExam] = useState({ subject: '', date: '' });

  // Privacy state
  const [privacy, setPrivacy] = useState(privacySettings);

  // Show save message temporarily
  const showSaveMessage = (message) => {
    setSaveMessage(message);
    setTimeout(() => setSaveMessage(''), 2000);
  };

  // Avatar helpers
  const getAvatarUrl = (style, seed) => {
    return `https://api.dicebear.com/7.x/${style}/svg?seed=${seed}`;
  };

  const regenerateAvatar = () => {
    setAvatarSeed(Date.now().toString());
  };

  // Calendar helpers
  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  const getDaysInMonth = (month, year) => new Date(year, month + 1, 0).getDate();
  const getFirstDayOfMonth = (month, year) => new Date(year, month, 1).getDay();

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
    setShowAddExam(true);
  };

  // Save handlers
  const saveProfile = () => {
    updateProfile({
      name: profileData.name,
      classLevel: profileData.classLevel,
      username: profileData.username,
    });
    showSaveMessage('Profile saved!');
  };

  const addSubject = () => {
    if (newSubject.name && newSubject.marks) {
      const marks = parseInt(newSubject.marks);
      if (marks >= 0 && marks <= 100) {
        const updatedSubjects = [...subjects, { ...newSubject, marks }];
        setSubjects(updatedSubjects);
        updateAcademics({ subjects: updatedSubjects });
        setNewSubject({ name: '', marks: '' });
        setShowAddSubject(false);
        showSaveMessage('Subject added!');
      }
    }
  };

  const removeSubject = (index) => {
    const updatedSubjects = subjects.filter((_, i) => i !== index);
    setSubjects(updatedSubjects);
    updateAcademics({ subjects: updatedSubjects });
    showSaveMessage('Subject removed!');
  };

  const saveAvatar = () => {
    updateProfile({
      avatarSeed,
      avatarStyle,
    });
    showSaveMessage('Avatar saved!');
  };

  const addExam = () => {
    if (newExam.subject && newExam.date) {
      const updatedExams = [...exams, { ...newExam, id: Date.now() }];
      setExams(updatedExams);
      updateCalendar({ exams: updatedExams });
      setNewExam({ subject: '', date: '' });
      setShowAddExam(false);
      setSelectedDate(null);
      showSaveMessage('Exam added!');
    }
  };

  const removeExam = (id) => {
    const updatedExams = exams.filter(exam => exam.id !== id);
    setExams(updatedExams);
    updateCalendar({ exams: updatedExams });
    showSaveMessage('Exam removed!');
  };

  const togglePrivacy = (key) => {
    const updated = { ...privacy, [key]: !privacy[key] };
    setPrivacy(updated);
    updatePrivacySettings(updated);
    showSaveMessage('Privacy setting updated!');
  };

  // Generate calendar grid
  const daysInMonth = getDaysInMonth(currentMonth, currentYear);
  const firstDay = getFirstDayOfMonth(currentMonth, currentYear);
  const calendarDays = [];
  for (let i = 0; i < firstDay; i++) calendarDays.push(null);
  for (let day = 1; day <= daysInMonth; day++) calendarDays.push(day);

  // Render tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Name
              </label>
              <Input
                type="text"
                value={profileData.name}
                onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                placeholder="Enter your name"
                className="h-12"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <Input
                type="text"
                value={profileData.username}
                onChange={(e) => setProfileData({ 
                  ...profileData, 
                  username: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '') 
                })}
                placeholder="your_username"
                className="h-12"
              />
              <p className="text-xs text-gray-500 mt-1">Letters, numbers, and underscores only</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Class Level
              </label>
              <div className="grid grid-cols-4 gap-2">
                {classesData.classes.map((cls) => (
                  <button
                    key={cls.level}
                    type="button"
                    onClick={() => setProfileData({ ...profileData, classLevel: cls.level })}
                    className={`p-3 rounded-lg border-2 text-center transition-all duration-200 ${
                      profileData.classLevel === cls.level
                        ? 'border-gray-900 bg-gray-900 text-white'
                        : 'border-gray-200 hover:border-gray-400'
                    }`}
                  >
                    <span className="font-medium">{cls.level}</span>
                  </button>
                ))}
              </div>
            </div>

            <Button onClick={saveProfile} className="w-full h-12">
              <Save className="w-4 h-4 mr-2" />
              Save Profile
            </Button>
          </div>
        );

      case 'academics':
        return (
          <div className="space-y-6">
            <p className="text-sm text-gray-500">
              Track your previous year subjects and marks to help personalize your learning.
            </p>

            {subjects.length > 0 && (
              <div className="space-y-3">
                {subjects.map((subject, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-xl"
                  >
                    <div>
                      <p className="font-medium text-gray-800">{subject.name}</p>
                      <p className="text-sm text-gray-500">{subject.marks} marks</p>
                    </div>
                    <button
                      onClick={() => removeSubject(index)}
                      className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {showAddSubject ? (
              <div className="p-4 border-2 border-dashed border-gray-300 rounded-xl space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Subject</label>
                  <Input
                    type="text"
                    value={newSubject.name}
                    onChange={(e) => setNewSubject({ ...newSubject, name: e.target.value })}
                    placeholder="Enter subject name"
                    className="h-12"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Marks (out of 100)</label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={newSubject.marks}
                    onChange={(e) => setNewSubject({ ...newSubject, marks: e.target.value })}
                    placeholder="Enter marks"
                    className="h-12"
                  />
                </div>
                <div className="flex gap-2">
                  <Button onClick={addSubject} disabled={!newSubject.name || !newSubject.marks} className="flex-1">
                    Add Subject
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => { setShowAddSubject(false); setNewSubject({ name: '', marks: '' }); }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowAddSubject(true)}
                className="w-full p-4 border-2 border-dashed border-gray-300 rounded-xl text-gray-500 hover:text-gray-700 hover:border-gray-400 transition-colors flex items-center justify-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Add a subject
              </button>
            )}
          </div>
        );

      case 'avatar':
        return (
          <div className="space-y-6">
            {/* Avatar Preview */}
            <div className="flex justify-center">
              <div className="relative">
                <img
                  src={getAvatarUrl(avatarStyle, avatarSeed)}
                  alt="Avatar"
                  className="w-32 h-32 rounded-full bg-gray-100 border-4 border-white shadow-lg"
                />
                <button
                  type="button"
                  onClick={regenerateAvatar}
                  className="absolute -bottom-2 -right-2 w-10 h-10 bg-gray-900 text-white rounded-full flex items-center justify-center hover:bg-gray-700 transition-colors shadow-lg"
                >
                  <RefreshCw className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Style Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Choose a style
              </label>
              <div className="grid grid-cols-5 gap-2">
                {AVATAR_STYLES.map((style) => (
                  <button
                    key={style.id}
                    type="button"
                    onClick={() => setAvatarStyle(style.id)}
                    className={`flex flex-col items-center p-3 rounded-xl border-2 transition-all duration-200 ${
                      avatarStyle === style.id
                        ? 'border-gray-900 bg-gray-50'
                        : 'border-gray-200 hover:border-gray-400'
                    }`}
                  >
                    <img
                      src={getAvatarUrl(style.id, avatarSeed)}
                      alt={style.name}
                      className="w-10 h-10 mb-1"
                    />
                    <span className="text-xs text-gray-600">{style.name}</span>
                  </button>
                ))}
              </div>
            </div>

            <Button onClick={saveAvatar} className="w-full h-12">
              <Save className="w-4 h-4 mr-2" />
              Save Avatar
            </Button>
          </div>
        );

      case 'calendar':
        return (
          <div className="space-y-6">
            {/* 
             * TODO: Backend Integration
             * - GET /api/calendar/events - Fetch user's calendar events
             * - POST /api/calendar/events - Create new event
             * - DELETE /api/calendar/events/:id - Delete event
             * - PUT /api/calendar/events/:id - Update event
             */}
            
            {/* Header with Add Event Button */}
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Manage your exam dates and reminders
              </p>
              <Button 
                onClick={() => {
                  setSelectedDate(formatDate(new Date().getDate()));
                  setNewExam({ subject: '', date: formatDate(new Date().getDate()), type: 'exam' });
                  setShowAddExam(true);
                }}
                className="bg-orange-500 hover:bg-orange-600"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Event
              </Button>
            </div>

            {/* Calendar Grid */}
            <div className="border border-gray-200 rounded-xl overflow-hidden bg-white">
              {/* Month Navigation */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                <h3 className="text-xl font-semibold text-gray-800">
                  {MONTHS[currentMonth]} {currentYear}
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => navigateMonth(-1)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => navigateMonth(1)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Weekday Headers */}
              <div className="grid grid-cols-7 border-b border-gray-100">
                {WEEKDAYS.map((day, index) => (
                  <div 
                    key={day} 
                    className={`text-center text-xs font-medium text-gray-500 py-3 ${
                      index < 6 ? 'border-r border-gray-100' : ''
                    }`}
                  >
                    {day}
                  </div>
                ))}
              </div>

              {/* Calendar Grid with Events */}
              <div className="grid grid-cols-7">
                {calendarDays.map((day, index) => {
                  const isLastInRow = (index + 1) % 7 === 0;
                  const isInLastRow = index >= calendarDays.length - 7;
                  
                  if (day === null) {
                    return (
                      <div 
                        key={`empty-${index}`} 
                        className={`min-h-[100px] bg-gray-50 ${
                          !isLastInRow ? 'border-r border-gray-100' : ''
                        } ${!isInLastRow ? 'border-b border-gray-100' : ''}`}
                      />
                    );
                  }

                  const dayExams = getExamsForDate(day);
                  const isToday = new Date().getDate() === day && 
                                  new Date().getMonth() === currentMonth && 
                                  new Date().getFullYear() === currentYear;

                  return (
                    <div
                      key={day}
                      onClick={() => handleDateClick(day)}
                      className={`min-h-[100px] p-2 cursor-pointer transition-colors hover:bg-gray-50 ${
                        !isLastInRow ? 'border-r border-gray-100' : ''
                      } ${!isInLastRow ? 'border-b border-gray-100' : ''}`}
                    >
                      {/* Date Number */}
                      <div className="flex items-start justify-between mb-1">
                        <span 
                          className={`inline-flex items-center justify-center w-7 h-7 text-sm font-medium rounded-full ${
                            isToday 
                              ? 'bg-gray-900 text-white' 
                              : 'text-gray-700'
                          }`}
                        >
                          {day}
                        </span>
                      </div>
                      
                      {/* Events on this date */}
                      <div className="space-y-1">
                        {dayExams.slice(0, 3).map((exam, examIndex) => {
                          // Assign colors based on exam type or cycle through colors
                          const colors = [
                            { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-l-emerald-500' },
                            { bg: 'bg-pink-100', text: 'text-pink-700', border: 'border-l-pink-500' },
                            { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-l-blue-500' },
                            { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-l-amber-500' },
                            { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-l-purple-500' },
                          ];
                          const color = colors[examIndex % colors.length];
                          
                          return (
                            <div
                              key={exam.id}
                              className={`px-2 py-1 text-xs font-medium rounded ${color.bg} ${color.text} border-l-2 ${color.border} truncate`}
                              title={exam.subject}
                            >
                              {exam.subject}
                            </div>
                          );
                        })}
                        {dayExams.length > 3 && (
                          <div className="text-xs text-gray-500 pl-2">
                            +{dayExams.length - 3} more
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Add Event Modal/Form */}
            {showAddExam && (
              <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
                  {/* 
                   * TODO: Backend Integration
                   * - Validate event data
                   * - POST /api/calendar/events with event details
                   */}
                  <div className="flex items-center justify-between mb-6">
                    <h4 className="text-lg font-semibold text-gray-800">Add Event</h4>
                    <button 
                      onClick={() => { setShowAddExam(false); setSelectedDate(null); }} 
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <X className="w-5 h-5 text-gray-500" />
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
                      <div className="px-4 py-3 bg-gray-50 rounded-lg text-gray-700 font-medium">
                        {selectedDate}
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Event Name</label>
                      <Input
                        type="text"
                        value={newExam.subject}
                        onChange={(e) => setNewExam({ ...newExam, subject: e.target.value })}
                        placeholder="e.g., Mathematics Unit Test"
                        className="h-12"
                      />
                    </div>

                    <div className="flex gap-3 pt-2">
                      <Button 
                        variant="outline" 
                        onClick={() => { setShowAddExam(false); setSelectedDate(null); }}
                        className="flex-1 h-12"
                      >
                        Cancel
                      </Button>
                      <Button 
                        onClick={addExam} 
                        disabled={!newExam.subject} 
                        className="flex-1 h-12 bg-orange-500 hover:bg-orange-600"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Event
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Upcoming Events List */}
            {exams.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-3">All Events</h4>
                <div className="space-y-2">
                  {exams.map((exam, index) => {
                    const colors = [
                      { bg: 'bg-emerald-50', border: 'border-l-emerald-500', icon: 'bg-emerald-500' },
                      { bg: 'bg-pink-50', border: 'border-l-pink-500', icon: 'bg-pink-500' },
                      { bg: 'bg-blue-50', border: 'border-l-blue-500', icon: 'bg-blue-500' },
                      { bg: 'bg-amber-50', border: 'border-l-amber-500', icon: 'bg-amber-500' },
                      { bg: 'bg-purple-50', border: 'border-l-purple-500', icon: 'bg-purple-500' },
                    ];
                    const color = colors[index % colors.length];
                    
                    return (
                      <div
                        key={exam.id}
                        className={`flex items-center justify-between p-4 ${color.bg} border-l-4 ${color.border} rounded-lg`}
                      >
                        {/* 
                         * TODO: Backend Integration
                         * - DELETE /api/calendar/events/:id
                         */}
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${color.icon}`} />
                          <div>
                            <p className="font-medium text-gray-800">{exam.subject}</p>
                            <p className="text-sm text-gray-500">{exam.date}</p>
                          </div>
                        </div>
                        <button
                          onClick={(e) => { e.stopPropagation(); removeExam(exam.id); }}
                          className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );

      case 'privacy':
        return (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 mb-6">
              Control your privacy preferences and data sharing settings.
            </p>

            {/* Privacy Toggle Items */}
            <div className="space-y-3">
              <div 
                onClick={() => togglePrivacy('showProfileToOthers')}
                className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-xl cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div>
                  <p className="font-medium text-gray-800">Show Profile to Others</p>
                  <p className="text-sm text-gray-500">Allow other students to view your profile</p>
                </div>
                <div className={`w-12 h-7 rounded-full transition-colors relative ${privacy.showProfileToOthers ? 'bg-green-500' : 'bg-gray-300'}`}>
                  <div className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow transition-transform ${privacy.showProfileToOthers ? 'translate-x-6' : 'translate-x-1'}`} />
                </div>
              </div>

              <div 
                onClick={() => togglePrivacy('allowNotifications')}
                className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-xl cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div>
                  <p className="font-medium text-gray-800">Allow Notifications</p>
                  <p className="text-sm text-gray-500">Receive updates about your learning progress</p>
                </div>
                <div className={`w-12 h-7 rounded-full transition-colors relative ${privacy.allowNotifications ? 'bg-green-500' : 'bg-gray-300'}`}>
                  <div className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow transition-transform ${privacy.allowNotifications ? 'translate-x-6' : 'translate-x-1'}`} />
                </div>
              </div>

              <div 
                onClick={() => togglePrivacy('shareProgressWithTeacher')}
                className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-xl cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div>
                  <p className="font-medium text-gray-800">Share Progress with Teacher</p>
                  <p className="text-sm text-gray-500">Let your teacher track your learning progress</p>
                </div>
                <div className={`w-12 h-7 rounded-full transition-colors relative ${privacy.shareProgressWithTeacher ? 'bg-green-500' : 'bg-gray-300'}`}>
                  <div className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow transition-transform ${privacy.shareProgressWithTeacher ? 'translate-x-6' : 'translate-x-1'}`} />
                </div>
              </div>

              <div 
                onClick={() => togglePrivacy('dataCollectionConsent')}
                className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-xl cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div>
                  <p className="font-medium text-gray-800">Anonymous Data Collection</p>
                  <p className="text-sm text-gray-500">Help improve the app with anonymous usage data</p>
                </div>
                <div className={`w-12 h-7 rounded-full transition-colors relative ${privacy.dataCollectionConsent ? 'bg-green-500' : 'bg-gray-300'}`}>
                  <div className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow transition-transform ${privacy.dataCollectionConsent ? 'translate-x-6' : 'translate-x-1'}`} />
                </div>
              </div>
            </div>

            <p className="text-xs text-gray-400 mt-6">
              Your privacy settings are automatically saved. Changes take effect immediately.
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-gray-800">Settings</h1>
              <p className="text-sm text-gray-500">Manage your profile and preferences</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex gap-8">
          {/* Sidebar Tabs */}
          <div className="w-56 flex-shrink-0">
            <nav className="space-y-1 sticky top-8">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                      isActive 
                        ? 'bg-gray-900 text-white shadow-lg' 
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <span className="font-medium">{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="flex-1">
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-800">
                  {TABS.find(t => t.id === activeTab)?.label}
                </h2>
                {saveMessage && (
                  <span className="text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full">
                    {saveMessage}
                  </span>
                )}
              </div>
              {renderTabContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
