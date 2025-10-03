export interface Enterprise {
  id: number;
  nome_fantasia: string;
  cnpj: string;
  nome_admin_empresa: string;
  cpf_adm: string;
  telefone: string;
  status?: 'pending' | 'approved' | 'rejected';
  rejection_reason?: string;
  // email: string;
  // senha: string;
}

export type EnterpriseFormData = Omit<Enterprise, 'id' | 'creation_date' | 'user_id' | 'status' | 'rejection_reason'>;