import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface DemoUser {
  id: string;
  name: string;
  role: "customer" | "adjuster" | "admin";
  email: string;
  active_policy_id?: string;
  description?: string;
}

export const PRESET_DEMO_USERS: DemoUser[] = [
  { id: "U-101", name: "Rahul Desai", role: "customer", email: "rahul.desai@example.com", description: "Health Guard Standard Policyholder" },
  { id: "U-102", name: "Priya Sharma", role: "customer", email: "priya.sharma@example.com", description: "Auto Shield Comprehensive Policyholder" },
  { id: "U-103", name: "Amit Patel", role: "customer", email: "amit.patel@example.com", description: "Home Secure Basic Policyholder" },
  { id: "U-104", name: "Neha Gupta", role: "customer", email: "neha.gupta@example.com", description: "Multi-Policy Customer" },
  { id: "U-900", name: "Vikram Singh", role: "adjuster", email: "vikram.adjuster@akira-insurance.internal", description: "Senior Claims Adjuster" },
  { id: "U-901", name: "Akira Admin", role: "admin", email: "admin@akira-insurance.internal", description: "Underwriting & Operations Administrator" },
];

interface PersonaState {
  currentPersonaId: string;
  currentUser: DemoUser;
  availableUsers: DemoUser[];
  setPersona: (user: DemoUser) => void;
  setPersonaById: (id: string) => void;
  setAvailableUsers: (users: DemoUser[]) => void;
}

export const usePersonaStore = create<PersonaState>()(
  persist(
    (set, get) => ({
      currentPersonaId: "U-101",
      currentUser: PRESET_DEMO_USERS[0],
      availableUsers: PRESET_DEMO_USERS,
      setPersona: (user: DemoUser) => {
        set({ currentPersonaId: user.id, currentUser: user });
      },
      setPersonaById: (id: string) => {
        const found = get().availableUsers.find((u) => u.id === id) || PRESET_DEMO_USERS.find((u) => u.id === id);
        if (found) {
          set({ currentPersonaId: found.id, currentUser: found });
        }
      },
      setAvailableUsers: (users: DemoUser[]) => {
        set({ availableUsers: users.length > 0 ? users : PRESET_DEMO_USERS });
      },
    }),
    {
      name: "akira-persona-storage",
    }
  )
);
