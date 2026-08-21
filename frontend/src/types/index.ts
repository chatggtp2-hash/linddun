export type Role = 'ADMIN' | 'ASSESSOR' | 'REVIEWER'

export interface User {
  id: string
  email: string
  full_name: string
  role: Role
  is_active: boolean
}

export interface TreeNode {
  id: string
  code: string
  name: string
  risk: string
  score: number
  question_count: number
  evidence_count: number
  children: TreeNode[]
}

export interface Category {
  id: string
  code: string
  name: string
  description?: string
  display_order: number
}

export interface QuestionOption {
  id?: string
  label: string
  value: string
  risk_score: number
  risk_level: string
  display_order: number
}

export interface QuestionMapping {
  id?: string
  category_id: string
  node_id?: string | null
}

export interface Question {
  id: string
  text: string
  help_text?: string
  question_type: 'YES_NO' | 'SINGLE_CHOICE' | 'MULTIPLE_CHOICE' | 'TEXT'
  weight: number
  display_order: number
  is_mandatory: boolean
  is_active: boolean
  options: QuestionOption[]
  mappings: QuestionMapping[]
}

export interface Assessment {
  id: string
  name: string
  description?: string
  status: string
  owner_id: string
  overall_score?: number
  overall_risk_level?: string
  created_at: string
  submitted_at?: string
}

export interface AssessmentQuestionItem {
  question_id: string
  text: string
  help_text?: string
  question_type: string
  is_mandatory: boolean
  options: { id: string; label: string; value: string }[]
  mapped_category?: string
  existing_answer?: { selected_option_id?: string; text_response?: string }
}

export interface CategoryResult {
  category_id: string
  category_name: string
  score: number
  risk_level: string
}

export interface AssessmentResult {
  assessment: Assessment
  category_results: CategoryResult[]
  top_threats: { name: string; risk_level: string; score: number }[]
  recommendations: string[]
}

export interface Evidence {
  id: string
  assessment_id: string
  question_id?: string
  node_id?: string
  file_name: string
  file_type: string
  file_size: number
  uploaded_at: string
}
