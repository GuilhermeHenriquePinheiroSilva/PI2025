import { Component } from '@angular/core';
import { FooterComponent } from '../shared/footer/footer.component';
import { RouterLink } from '@angular/router';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';



@Component({
  selector: 'app-search',
  standalone: true,
  imports: [
    NavBarComponent,
    FooterComponent,
    RouterLink,
  ],
  templateUrl: './search.component.html',
  styleUrl: './search.component.css'
})
export class SearchComponent {

}
