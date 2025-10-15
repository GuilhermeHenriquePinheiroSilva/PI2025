// Define a estrutura do cabeçalho do pedido, que será aninhada no item
export interface OrderInfo {
  owner_name: string;
  created_at: string; // ou Date
}

// Define a estrutura de um item dentro do pedido
export interface OrderItem {
  id: string; // UUID
  register_giftcard_id: string; // UUID
  quantity: number;
  unit_price: number;
  final_giftcard_codes: string | null;
  used_codes: string | null; // <-- CAMPO ADICIONADO
  status: 'VALID' | 'USED' | 'PARTIALLY_USED';
  // Adiciona uma referência ao produto para facilitar a exibição
  original_giftcard: {
    title: string;
    imageUrl: string;
    valor: number;
  };
  // Adiciona a referência ao pedido pai
  order: OrderInfo; // <-- CAMPO ADICIONADO
}

// Define a estrutura do cabeçalho do pedido principal
export interface Order {
  id: string; // UUID
  owner_id: number;
  owner_name: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'REFUNDED';
  total_amount: number;
  created_at: string; // ou Date
  items: OrderItem[];
}