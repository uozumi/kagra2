export interface User {
  id: string;
  email: string;
  name: string | null;
  created_at: string;
  is_system_admin: boolean;
} 