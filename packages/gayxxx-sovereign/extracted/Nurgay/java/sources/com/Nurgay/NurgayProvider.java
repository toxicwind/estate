package com.Nurgay;

/* JADX INFO: compiled from: NurgayProvider.kt */
/* JADX INFO: loaded from: classes.dex */
@com.lagradost.cloudstream3.plugins.CloudstreamPlugin
@kotlin.Metadata(d1 = {"\u0000\u0018\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\b\u0007\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u0010\u0010\u0004\u001a\u00020\u00052\u0006\u0010\u0006\u001a\u00020\u0007H\u0016¨\u0006\b"}, d2 = {"Lcom/Nurgay/NurgayProvider;", "Lcom/lagradost/cloudstream3/plugins/Plugin;", "<init>", "()V", "load", "", "context", "Landroid/content/Context;", "Nurgay"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final class NurgayProvider extends com.lagradost.cloudstream3.plugins.Plugin {
    public void load(@org.jetbrains.annotations.NotNull android.content.Context context) {
        registerMainAPI(new com.Nurgay.Nurgay());
        registerExtractorAPI(new com.Nurgay.Bigwarp());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.Voe());
        registerExtractorAPI(new com.Nurgay.VoeExtractor());
        registerExtractorAPI(new com.Nurgay.dsio());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DoodstreamCom());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.Doodspro());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DoodLiExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DoodToExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DoodPmExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DoodCxExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.doodre());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DoodShExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DoodSoExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DoodWatchExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DoodWfExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DoodWsExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.D0000d());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.D000dCom());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.Ds2play());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.Ds2video());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.DSVPlay());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.Dooodster());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.Dooood());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.vide0());
        registerExtractorAPI(new com.Nurgay.ListMirror());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.MixDrop());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.MxDrop());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.MixDropCv());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.mdfx9dc8n());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.MixDropIs());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Nurgay.MixDropAg());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.StreamTape());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.VinovoTo());
        registerExtractorAPI(new com.Nurgay.VidNest());
        registerExtractorAPI(new com.Nurgay.Videzz());
    }
}
