import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificationService } from '../../../services/notification.service';
import { OrderService } from '../../../services/order.service';
import { Order, OrderItem } from '../../models/order.model'; // Importe OrderItem também
import { Router, ActivatedRoute } from '@angular/router';
import { CartService } from '../../../services/cart.service';

@Component({
  selector: 'app-my-purchases',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './my-purchases.component.html',
  styleUrls: ['./my-purchases.component.css']
})
export class MyPurchasesComponent implements OnInit {
  approvedOrders: Order[] = [];
  pendingOrders: Order[] = [];
  isLoading = true;
  revealedCodes: { [itemId: string]: string } = {};

  // --- DICIONÁRIO DE TRUÇÔES ADICIONADO ---
  statusTranslations: { [key: string]: string } = {
    // Status do Pedido
    'APPROVED': 'Aprovado',
    'PENDING': 'Pendente',
    'REJECTED': 'Rejeitado',
    'EXPIRED': 'Expirado',
    'REFUNDED': 'Estornado',
    // Status do Item/Código
    'VALID': 'Válido',
    'USED': 'Utilizado',
    'PARTIALLY_USED': 'Parcialmente Utilizado'
  };

  constructor(
    private orderService: OrderService,
    private notificationService: NotificationService,
    private router: Router,
    private route: ActivatedRoute,
    private cartService: CartService
  ) {}

  ngOnInit(): void {
    this.handlePaymentStatus();
    this.loadOrders();
  }

  // --- NOVA FUNÇÃO DE TRADUÇÃO ---
  translateStatus(status: string): string {
    return this.statusTranslations[status] || status;
  }

  private handlePaymentStatus(): void {
    this.route.queryParamMap.subscribe(params => {
        const status = params.get('status');
        if (status === 'approved' && sessionStorage.getItem('paymentProcessed') !== 'true') {
            this.notificationService.show('Pagamento aprovado com sucesso!', 'success');
            this.cartService.clearCart();
            sessionStorage.setItem('paymentProcessed', 'true');
            this.router.navigate([], {
                relativeTo: this.route,
                queryParams: { status: null },
                queryParamsHandling: 'merge'
            });
        }
        if (!status) {
            sessionStorage.removeItem('paymentProcessed');
        }
    });
  }

  loadOrders(): void {
    this.isLoading = true;
    this.orderService.getMyOrders().subscribe({
      next: (data) => {
        this.approvedOrders = data.filter(order => order.status === 'APPROVED');
        this.pendingOrders = data.filter(order => order.status === 'PENDING');
        this.isLoading = false;
      },
      error: () => {
        this.notificationService.show('Erro ao carregar seu histórico de compras.', 'error');
        this.isLoading = false;
      }
    });
  }

  revealAndCopyCodes(item: OrderItem): void {
    const codes = item.final_giftcard_codes;
    if (!codes) {
        this.notificationService.show('Códigos ainda não disponíveis.', 'warning');
        return;
    }

    navigator.clipboard.writeText(codes).then(() => {
        this.revealedCodes[item.id] = codes;
        this.notificationService.show(`Códigos copiados!`, 'success');
        
        setTimeout(() => {
            delete this.revealedCodes[item.id];
        }, 5000);

    }).catch(err => {
        this.notificationService.show('Não foi possível copiar os códigos.', 'error');
    });
  }

  isRevealed(itemId: string): boolean {
      return itemId in this.revealedCodes;
  }
}