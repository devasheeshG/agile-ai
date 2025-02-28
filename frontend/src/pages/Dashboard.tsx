import React, { useState } from 'react';
import KanbanBoard from '../components/KanbanBoard';
import TeamCard from '../components/TeamCard';
import { useAuthStore } from '../store/authStore';
import { useTaskStore } from '../store/taskStore';
import { LayoutDashboard, CheckCircle2, Clock, AlertCircle, Flag, ClipboardList } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { user } = useAuthStore();
  const { tasks } = useTaskStore();
  const [activeTab, setActiveTab] = useState<'board' | 'overview'>('board');
  
  const myTasks = tasks.filter(task => task.assigneeId === user?.id);
  const todoCount = tasks.filter(task => task.status === 'todo').length;
  const inProgressCount = tasks.filter(task => task.status === 'inProgress').length;
  const reviewCount = tasks.filter(task => task.status === 'review').length;
  const doneCount = tasks.filter(task => task.status === 'done').length;
  
  const highPriorityCount = tasks.filter(task => task.priority === 'high' || task.priority === 'critical').length;
  const myTasksCount = myTasks.length;
  const myCompletedCount = myTasks.filter(task => task.status === 'done').length;
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        
        <div className="flex bg-secondary rounded-md p-1">
          <button 
            className={`px-4 py-1.5 rounded-md ${activeTab === 'overview' ? 'bg-primary text-white' : 'text-gray-400'}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={`px-4 py-1.5 rounded-md ${activeTab === 'board' ? 'bg-primary text-white' : 'text-gray-400'}`}
            onClick={() => setActiveTab('board')}
          >
            Board
          </button>
        </div>
      </div>
      
      {activeTab === 'overview' ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-400/20 flex items-center justify-center">
                <LayoutDashboard className="text-blue-400" />
              </div>
              <div>
                <p className="text-gray-400">Total Tasks</p>
                <h3 className="text-2xl font-bold">{tasks.length}</h3>
              </div>
            </div>
            
            <div className="card flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-yellow-400/20 flex items-center justify-center">
                <Clock className="text-yellow-400" />
              </div>
              <div>
                <p className="text-gray-400">In Progress</p>
                <h3 className="text-2xl font-bold">{inProgressCount}</h3>
              </div>
            </div>
            
            <div className="card flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-red-400/20 flex items-center justify-center">
                <Flag className="text-red-400" />
              </div>
              <div>
                <p className="text-gray-400">High Priority</p>
                <h3 className="text-2xl font-bold">{highPriorityCount}</h3>
              </div>
            </div>
            
            <div className="card flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-green-400/20 flex items-center justify-center">
                <CheckCircle2 className="text-green-400" />
              </div>
              <div>
                <p className="text-gray-400">Completed</p>
                <h3 className="text-2xl font-bold">{doneCount}</h3>
              </div>
            </div>
          </div>
          
          <TeamCard />
          
          <div className="card">
            <h2 className="text-xl font-bold mb-4">My Tasks</h2>
            
            {myTasks.length > 0 ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-400">Progress:</span>
                    <div className="w-48 h-2 bg-secondary rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary" 
                        style={{ width: `${(myCompletedCount / myTasksCount) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm">{myCompletedCount} of {myTasksCount}</span>
                  </div>
                </div>
                
                <div className="space-y-2">
                  {myTasks.map(task => (
                    <div key={task.id} className="bg-secondary p-3 rounded-md flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{task.title}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${
                            task.status === 'todo' ? 'bg-blue-400/20 text-blue-400' :
                            task.status === 'inProgress' ? 'bg-yellow-400/20 text-yellow-400' :
                            task.status === 'review' ? 'bg-purple-400/20 text-purple-400' :
                            'bg-green-400/20 text-green-400'
                          }`}>
                            {task.status === 'todo' ? <ClipboardList size={12} /> :
                             task.status === 'inProgress' ? <Clock size={12} /> :
                             task.status === 'review' ? <AlertCircle size={12} /> :
                             <CheckCircle2 size={12} />}
                            <span className="ml-1 capitalize">{task.status === 'inProgress' ? 'In Progress' : task.status}</span>
                          </span>
                          
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${
                            task.priority === 'low' ? 'bg-blue-400/20 text-blue-400' :
                            task.priority === 'medium' ? 'bg-yellow-400/20 text-yellow-400' :
                            task.priority === 'high' ? 'bg-orange-400/20 text-orange-400' :
                            'bg-red-400/20 text-red-400'
                          }`}>
                            <Flag size={12} />
                            <span className="ml-1 capitalize">{task.priority}</span>
                          </span>
                        </div>
                      </div>
                      
                      {task.dueDate && (
                        <div className="text-sm text-gray-400">
                          Due: {new Date(task.dueDate).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-gray-400">
                <p>No tasks assigned to you yet.</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div>
          <TeamCard />
          
          <div className="mt-6">
            <h2 className="text-xl font-bold mb-4">Project Board</h2>
            <div className="h-[calc(100vh-300px)]">
              <KanbanBoard />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;