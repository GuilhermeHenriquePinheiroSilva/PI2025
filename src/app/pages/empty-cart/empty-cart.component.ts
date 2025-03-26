import { Component } from '@angular/core';
import { FooterComponent } from '../shared/footer/footer.component';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';

@Component({
  selector: 'app-empty-cart',
  standalone: true,
  imports: [NavBarComponent,
            FooterComponent],
  templateUrl: './empty-cart.component.html',
  styleUrl: './empty-cart.component.css'
})
export class EmptyCartComponent {

}
