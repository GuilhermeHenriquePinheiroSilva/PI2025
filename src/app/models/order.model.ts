// Define a estrutura do Dono (Comprador) aninhada
export interface OwnerInfo {
  id: number;
  username: string;
}

// Define a estrutura do cabeçalho do pedido, que será aninhada no item
export interface OrderInfo {
  owner_id: number; // <-- ID do comprador
  owner?: OwnerInfo; // <-- Objeto aninhado com detalhes do comprador (incluindo username)
  created_at: string; // ou Date
  status?: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'REFUNDED'; // Status do pedido pai
}

// Define a estrutura de um item dentro do pedido
export interface OrderItem {
  id: string; // UUID
  register_giftcard_id: string; // UUID
  enterprise_id: number;
  quantity: number;
  unit_price: number; // Preço de venda unitário pago pelo cliente
  seller_amount: number; // Valor a repassar para a empresa
  final_giftcard_codes: string | null; // Códigos gerados/atribuídos após aprovação
  used_codes: string | null; // Códigos que já foram marcados como usados
  status: 'VALID' | 'USED' | 'PARTIALLY_USED'; // Status do código em si
  original_giftcard: { // Detalhes do produto Gift Card
    title: string;
    imageUrl: string | null; // Tornar opcional se puder ser nulo
    valor: number; // Preço de venda unitário
    desired_amount: number; // Valor desejado pela empresa
  };
  order?: OrderInfo; // Informações do pedido pai (data, status, comprador)
}

// Define a estrutura do cabeçalho do pedido principal (usado em /orders/me)
export interface Order {
  id: string; // UUID
  owner_id: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'REFUNDED'; // Status geral do pedido
  total_amount: number; // Valor total pago pelo cliente
  net_amount?: number; // Valor líquido recebido (opcional, pode vir do MP)
  created_at: string; // ou Date
  items: OrderItem[]; // Lista de itens do pedido
  owner?: OwnerInfo; // Detalhes do comprador no nível do pedido principal
}