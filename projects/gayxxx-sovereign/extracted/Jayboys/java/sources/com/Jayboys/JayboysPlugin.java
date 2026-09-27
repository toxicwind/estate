package com.Jayboys;

/* JADX INFO: compiled from: JavboysPlugin.kt */
/* JADX INFO: loaded from: classes.dex */
@com.lagradost.cloudstream3.plugins.CloudstreamPlugin
@kotlin.Metadata(d1 = {"\u0000\u0018\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\b\u0007\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u0010\u0010\u0004\u001a\u00020\u00052\u0006\u0010\u0006\u001a\u00020\u0007H\u0016¨\u0006\b"}, d2 = {"Lcom/Jayboys/JayboysPlugin;", "Lcom/lagradost/cloudstream3/plugins/Plugin;", "<init>", "()V", "load", "", "context", "Landroid/content/Context;", "Jayboys"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final class JayboysPlugin extends com.lagradost.cloudstream3.plugins.Plugin {
    public void load(@org.jetbrains.annotations.NotNull android.content.Context context) {
        registerMainAPI(new com.Jayboys.Jayboys1());
        registerMainAPI(new com.Jayboys.Jayboys2());
        registerMainAPI(new com.Jayboys.Jayboys3());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.dsio());
        registerExtractorAPI(new com.Jayboys.VoeExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.Voe());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.boynextdoor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.crystal());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.StreamTape());
        registerExtractorAPI(new com.Jayboys.yi069website());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.DoodLaExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.DoodstreamCom());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.playmogo());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.vide0());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.tapepops());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.FileMoon());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.FilemoonV2());
        registerExtractorAPI(new com.Jayboys.Bysekoze());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.ByseSX());
        registerExtractorAPI(new com.Jayboys.Jgvcdn());
        registerExtractorAPI(new com.Jayboys.Base64Extractor());
        registerExtractorAPI(new com.Jayboys.JP());
        registerExtractorAPI(new com.Jayboys.jaygo());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.hypeboy());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.do7go());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Jayboys.myvidplay());
    }
}
