import { useColorScheme } from "react-native";
export const palette={paper:"#F4F3EE",paperDark:"#10110F",ink:"#171813",muted:"#74766D",line:"#DDDCD4",card:"#FCFCF8",accent:"#C8FF45",soft:"#E9F6C8"};
export function useTheme(){const dark=useColorScheme()==="dark";return{dark,bg:dark?palette.paperDark:palette.paper,card:dark?"#191A17":palette.card,text:dark?"#F4F4EE":palette.ink,muted:dark?"#9B9D94":palette.muted,line:dark?"#2D2F29":palette.line,accent:palette.accent};}
