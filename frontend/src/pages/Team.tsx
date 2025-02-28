import React, { useState, useEffect } from 'react';
import { useTeamStore } from '../store/teamStore';
import { useAuthStore } from '../store/authStore';
import { Users, UserPlus, X, Upload, Crown } from 'lucide-react';

const Team: React.FC = () => {
  const { team, createTeam, addMember, removeMember, setTeamLead } = useTeamStore();
  const { user } = useAuthStore();
  const [showAddMemberForm, setShowAddMemberForm] = useState(false);
  const [memberName, setMemberName] = useState('');
  const [memberRole, setMemberRole] = useState('');
  const [memberResume, setMemberResume] = useState<File | null>(null);
  
  // Create a default team if none exists
  useEffect(() => {
    if (!team) {
      createTeam("My Team");
    }
  }, [team, createTeam]);
  
  const handleAddMember = (e: React.FormEvent) => {
    e.preventDefault();
    if (memberName.trim() && memberRole.trim()) {
      addMember({
        name: memberName,
        role: memberRole,
        resume: memberResume
      });
      setMemberName('');
      setMemberRole('');
      setMemberResume(null);
      setShowAddMemberForm(false);
    }
  };
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setMemberResume(e.target.files[0]);
    }
  };
  
  const handlePromoteToLead = (memberId: string) => {
    if (confirm('Are you sure you want to promote this member to team lead?')) {
      setTeamLead(memberId);
    }
  };
  
  const isTeamLead = user?.role === 'lead';
  
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Team Management</h1>
      
      <div className="card">
        <div className="flex flex-col space-y-4 mb-4">
          <div className="flex items-center gap-2">
            <Users className="text-primary" />
            <h2 className="text-xl font-bold">Team Members</h2>
          </div>
          
          {isTeamLead && (
            <button 
              className="btn btn-primary flex items-center gap-2 self-start"
              onClick={() => setShowAddMemberForm(true)}
            >
              <UserPlus size={18} />
              <span>Add Member</span>
            </button>
          )}
        </div>
        
        {showAddMemberForm && (
          <div className="mb-6 bg-secondary p-4 rounded-lg border border-border">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">Add New Team Member</h3>
              <button 
                className="text-gray-400 hover:text-white"
                onClick={() => setShowAddMemberForm(false)}
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleAddMember}>
              <div className="mb-4">
                <label htmlFor="memberName" className="block mb-2">Name</label>
                <input
                  type="text"
                  id="memberName"
                  className="input w-full"
                  value={memberName}
                  onChange={(e) => setMemberName(e.target.value)}
                  placeholder="Enter member name"
                  required
                />
              </div>
              <div className="mb-4">
                <label htmlFor="memberRole" className="block mb-2">Role</label>
                <select
                  id="memberRole"
                  className="input w-full"
                  value={memberRole}
                  onChange={(e) => setMemberRole(e.target.value)}
                  required
                >
                  <option value="">Select a role</option>
                  <option value="Frontend Developer">Frontend Developer</option>
                  <option value="Backend Developer">Backend Developer</option>
                  <option value="UI/UX Designer">UI/UX Designer</option>
                  <option value="Project Manager">Project Manager</option>
                  <option value="QA Engineer">QA Engineer</option>
                </select>
              </div>
              <div className="mb-4">
                <label htmlFor="memberResume" className="block mb-2">Resume (PDF)</label>
                <div className="border border-dashed border-border rounded-md p-4 text-center">
                  <input
                    type="file"
                    id="memberResume"
                    className="hidden"
                    accept=".pdf"
                    onChange={handleFileChange}
                  />
                  <label htmlFor="memberResume" className="cursor-pointer flex flex-col items-center">
                    <Upload className="mb-2 text-primary" />
                    {memberResume ? (
                      <span>{memberResume.name}</span>
                    ) : (
                      <span className="text-gray-400">Click to upload PDF</span>
                    )}
                  </label>
                </div>
              </div>
              <button type="submit" className="btn btn-primary">Add Member</button>
            </form>
          </div>
        )}
        
        {team && team.members.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {team.members.map(member => (
              <div key={member.id} className="bg-secondary rounded-lg p-4 border border-border">
                <div className="flex justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-lg font-bold relative">
                      {member.name.charAt(0).toUpperCase()}
                      {team.leadId === member.id && (
                        <span className="absolute -top-1 -right-1 bg-yellow-400 rounded-full p-0.5">
                          <Crown size={12} className="text-background" />
                        </span>
                      )}
                    </div>
                    <div>
                      <h3 className="font-medium text-lg flex items-center gap-2">
                        {member.name}
                        {team.leadId === member.id && (
                          <span className="text-xs bg-yellow-400/20 text-yellow-400 px-2 py-0.5 rounded-full flex items-center gap-1">
                            <Crown size={10} />
                            <span>Lead</span>
                          </span>
                        )}
                      </h3>
                      <p className="text-gray-400">{member.role}</p>
                    </div>
                  </div>
                  
                  {isTeamLead && (
                    <div className="flex items-center gap-2">
                      {team.leadId !== member.id && (
                        <button 
                          className="text-yellow-400 hover:text-yellow-300"
                          onClick={() => handlePromoteToLead(member.id)}
                          title="Promote to Team Lead"
                        >
                          <Crown size={18} />
                        </button>
                      )}
                      
                      <button 
                        className="text-red-400 hover:text-red-300"
                        onClick={() => removeMember(member.id)}
                      >
                        <X size={20} />
                      </button>
                    </div>
                  )}
                </div>
                
                {member.resume && (
                  <div className="mt-3 text-sm">
                    <p className="text-gray-400">Resume: {member.resume.name}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <p>No team members yet. Add members to your team.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Team;