// Define a estrutura do cabeçalho do pedido, que será aninhada no item
export interface OrderInfo {
  // owner_name: string; <-- Removido
  owner_id: number; // <-- ADICIONADO
  created_at: string; // ou Date
}

// Define a estrutura de um item dentro do pedido
export interface OrderItem {
  id: string; // UUID
  register_giftcard_id: string; // UUID
  enterprise_id: number;
  quantity: number;
  unit_price: number; // Preço de venda
  seller_amount: number; // Valor a repassar
  final_giftcard_codes: string | null;
  used_codes: string | null;
  status: 'VALID' | 'USED' | 'PARTIALLY_USED';
  original_giftcard: {
    title: string;
    imageUrl: string;
    valor: number;
    desired_amount: number;
  };
  order: OrderInfo; // Agora OrderInfo tem owner_id
}

// Define a estrutura do cabeçalho do pedido principal
export interface Order {
  id: string; // UUID
  owner_id: number;
  // owner_name: string; // Removido
  enterprise_id?: number; // Removido ou opcional
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'REFUNDED';
  total_amount: number;
  net_amount?: number;
  created_at: string; // ou Date
  items: OrderItem[];
}

